"""
Base types for extensions refactor
"""

import warnings
from functools import wraps

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from feincms.utils import get_object


class ExtensionsMixin(object):
    @property
    def _feincms_extensions(self):
        warnings.warn(
            'Start using _extensions instead of _feincms_extensions'
            ' today!',
            DeprecationWarning, stacklevel=2)

        return set(self._extensions)

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

            if isinstance(ext, six.string_types):
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
                warnings.warn(
                    '%r is a extension in legacy format.'
                    ' Support for legacy extensions will be removed in'
                    ' FeinCMS v1.9. Convert your extensions to'
                    ' feincms.extensions.Extension now.' % extension,
                    DeprecationWarning)
                cls._extensions.append(LegacyExtension(cls, extension=extension))


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


def _ensure_list(cls, attribute):
    if cls is None:
        return
    value = getattr(cls, attribute, ()) or ()
    setattr(cls, attribute, list(value))


class LegacyExtension(Extension):
    """
    Wrapper for legacy extensions
    """

    #: Legacy extension function
    extension = None

    def handle_model(self):
        self.fieldsets = []
        self.filter_horizontal = []
        self.filter_vertical = []
        self.list_display = []
        self.list_filter = []
        self.raw_id_fields = []
        self.search_fields = []

        self.extension_options = []
        self.known_keys = self.__dict__.keys()

        self.extension(self.model, self)

    def handle_modeladmin(self, modeladmin):
        if self.fieldsets:
            _ensure_list(modeladmin, 'fieldsets')
            modeladmin.fieldsets.extend(self.fieldsets)
        if self.filter_horizontal:
            _ensure_list(modeladmin, 'filter_horizontal')
            modeladmin.filter_horizontal.extend(self.filter_horizontal)
        if self.filter_vertical:
            _ensure_list(modeladmin, 'filter_vertical')
            modeladmin.filter_vertical.extend(self.filter_vertical)
        if self.list_display:
            _ensure_list(modeladmin, 'list_display')
            modeladmin.list_display.extend(self.list_display)
        if self.list_filter:
            _ensure_list(modeladmin, 'list_filter')
            modeladmin.list_filter.extend(self.list_filter)
        if self.raw_id_fields:
            _ensure_list(modeladmin, 'raw_id_fields')
            modeladmin.raw_id_fields.extend(self.raw_id_fields)
        if self.search_fields:
            _ensure_list(modeladmin, 'search_fields')
            modeladmin.search_fields.extend(self.search_fields)

        if self.extension_options:
            for f in self.extension_options:
                modeladmin.add_extension_options(*f)

        for key, value in self.__dict__.items():
            if key not in self.known_keys:
                setattr(modeladmin.__class__, key, value)

    def add_extension_options(self, *f):
        if f:
            self.extension_options.append(f)


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

    # queryset is renamed to get_queryset in Django 1.6
    fn = "get_queryset" if hasattr(modeladmin, "get_queryset") else "queryset"
    setattr(modeladmin, fn, do_wrap(getattr(modeladmin, fn)))
