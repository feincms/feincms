"""
Base types for extensions refactor
"""

import warnings

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured

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

        if not hasattr(cls, '_feincms_extensions'):
            cls._feincms_extensions = set()

        here = cls.__module__.split('.')[:-1]
        search_paths = [
            '.'.join(here + ['extensions']),
            '.'.join(here[:-1] + ['extensions']),
            'feincms.module.extensions',
            ]

        for ext in extensions:
            if ext in cls._feincms_extensions:
                continue

            extension = None

            if isinstance(ext, basestring):
                paths = [ext, '%s.register' % ext] + [
                    '%s.%s.register' % (path, ext) for path in search_paths]

                for path in paths:
                    try:
                        extension = get_object(path)
                        break
                    except (AttributeError, ImportError):
                        pass

                    """
                    warnings.warn(
                        'Using short names for extensions has been'
                        ' deprecated and will be removed in'
                        ' FeinCMS v1.8. Please provide the full'
                        ' python path to the extension'
                        ' %s instead (%s.%s).' % (ext, path, ext),
                        DeprecationWarning, stacklevel=2)
                    """

            if not extension:
                raise ImproperlyConfigured(
                    '%s is not a valid extension for %s' % (
                        ext, cls.__name__))

            if hasattr(extension, 'register'):
                extension = extension.register

            elif hasattr(extension, 'Extension'):
                extension = extension.Extension

            elif hasattr(extension, '__call__'):
                pass

            else:
                raise ImproperlyConfigured(
                    '%s is not a valid extension for %s' % (
                        ext, cls.__name__))

            if hasattr(extension, 'ident'):
                cls._extensions.append(extension(cls))
                cls._feincms_extensions.add(extension.ident)
            else:
                cls._extensions.append(OldSchoolExtension(cls, extension=extension))
                cls._feincms_extensions.add(ext)


class Extension(object):
    #: Unique identifier for this extension, will be added
    #: to ``cls._feincms_extensions`` to prevent double registration
    ident = ''

    def __init__(self, model, **kwargs):
        self.model = model
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise TypeError('%s() received an invalid keyword %r' % (
                    self.__class__.__name__, key))
            setattr(self, key, value)

        self.handle_model()

    def handle_model(self, model):
        raise NotImplementedError

    def handle_modeladmin(self, modeladmin):
        pass


class OldSchoolExtension(Extension):
    """
    Wrapper for old-school extensions
    """

    #: Old-school extension function
    extension = None

    def handle_model(self):
        self.fieldsets = []
        self.list_display = []
        self.list_filter = []
        self.search_fields = []

        self.extension(self.model, self)

    def handle_modeladmin(self, modeladmin):
        if self.fieldsets:
            modeladmin.fieldsets.extend(self.fieldsets)
        if self.list_display:
            modeladmin.list_display.extend(self.list_display)
        if self.list_filter:
            modeladmin.list_filter.extend(self.list_filter)
        if self.search_fields:
            modeladmin.search_fields.extend(self.search_fields)

    @classmethod
    def add_extension_options(cls, *f):
        if isinstance(f[-1], dict):     # called with a fieldset
            cls.fieldsets.insert(cls.fieldset_insertion_index, f)
            f[1]['classes'] = list(f[1].get('classes', []))
            f[1]['classes'].append('collapse')
        else:   # assume called with "other" fields
            cls.fieldsets[1][1]['fields'].extend(f)


class ExtensionModelAdmin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        super(ExtensionModelAdmin, self).__init__(*args, **kwargs)
        self.initialize_extensions()

    def initialize_extensions(self):
        if not hasattr(self, '_extensions_initialized'):
            self._extensions_initialized = True
            for extension in getattr(self.model, '_extensions', []):
                extension.handle_modeladmin(self)

    @classmethod
    def add_extension_options(cls, *f):
        if isinstance(f[-1], dict):     # called with a fieldset
            cls.fieldsets.insert(cls.fieldset_insertion_index, f)
            f[1]['classes'] = list(f[1].get('classes', []))
            f[1]['classes'].append('collapse')
        else:   # assume called with "other" fields
            cls.fieldsets[1][1]['fields'].extend(f)
