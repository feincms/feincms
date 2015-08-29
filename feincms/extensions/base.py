"""
Base types for extensions refactor
"""

from __future__ import absolute_import, unicode_literals

from functools import wraps
import inspect

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from feincms.utils import get_object


class ExtensionsMixin(object):
    @classmethod
    def register_extensions(cls, *extensions):
        """
        Register all extensions passed as arguments.

        Extensions should be specified as a string to the python module
        containing the extension. If it is a bundled extension of FeinCMS,
        you do not need to specify the full python module path -- only
        specifying the last part (f.e. ``'seo'`` or ``'translations'``) is
        sufficient.
        """

        if not hasattr(cls, '_extensions'):
            cls._extensions = []
            cls._extensions_seen = []

        for ext in extensions:
            if ext in cls._extensions:
                continue

            extension = None

            if inspect.isclass(ext) and issubclass(ext, Extension):
                extension = ext

            elif isinstance(ext, six.string_types):
                try:
                    extension = get_object(ext)
                except (AttributeError, ImportError, ValueError):
                    if not extension:
                        raise ImproperlyConfigured(
                            '%s is not a valid extension for %s' % (
                                ext, cls.__name__))

            if hasattr(extension, 'Extension'):
                extension = extension.Extension

            elif hasattr(extension, 'register'):
                extension = extension.register

            elif hasattr(extension, '__call__'):
                pass

            else:
                raise ImproperlyConfigured(
                    '%s is not a valid extension for %s' % (
                        ext, cls.__name__))

            if extension in cls._extensions_seen:
                continue
            cls._extensions_seen.append(extension)

            if hasattr(extension, 'handle_model'):
                cls._extensions.append(extension(cls))
            else:
                raise ImproperlyConfigured(
                    '%r is an invalid extension.' % extension)


class Extension(object):
    def __init__(self, model, **kwargs):
        self.model = model
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise TypeError('%s() received an invalid keyword %r' % (
                    self.__class__.__name__, key))
            setattr(self, key, value)

        self.handle_model()

    def handle_model(self):
        raise NotImplementedError

    def handle_modeladmin(self, modeladmin):
        pass


class ExtensionModelAdmin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        super(ExtensionModelAdmin, self).__init__(*args, **kwargs)
        self.initialize_extensions()

    def initialize_extensions(self):
        if not hasattr(self, '_extensions_initialized'):
            self._extensions_initialized = True
            for extension in getattr(self.model, '_extensions', []):
                extension.handle_modeladmin(self)

    def add_extension_options(self, *f):
        if self.fieldsets is None:
            return

        if isinstance(f[-1], dict):     # called with a fieldset
            self.fieldsets.insert(self.fieldset_insertion_index, f)
            f[1]['classes'] = list(f[1].get('classes', []))
            f[1]['classes'].append('collapse')
        elif f:   # assume called with "other" fields
            try:
                self.fieldsets[1][1]['fields'].extend(f)
            except IndexError:
                # Fall back to first fieldset if second does not exist
                # XXX This is really messy.
                self.fieldsets[0][1]['fields'].extend(f)

    def extend_list(self, attribute, iterable):
        extended = list(getattr(self, attribute, ()))
        extended.extend(iterable)
        setattr(self, attribute, extended)


def prefetch_modeladmin_get_queryset(modeladmin, *lookups):
    """
    Wraps default modeladmin ``get_queryset`` to prefetch related lookups.
    """
    def do_wrap(f):
        @wraps(f)
        def wrapper(request, *args, **kwargs):
            qs = f(request, *args, **kwargs)
            qs = qs.prefetch_related(*lookups)
            return qs
        return wrapper

    modeladmin.get_queryset = do_wrap(modeladmin.get_queryset)
