"""
Extend or modify the navigation with custom entries.

This extension allows the website administrator to select an extension
which processes, modifies or adds subnavigation entries. The bundled
``feincms_nav`` template tag knows how to collect navigation entries,
be they real Page instances or extended navigation entries.
"""

from __future__ import absolute_import, unicode_literals

from collections import OrderedDict
import types
import warnings

from django.db import models
from django.utils import six
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms.utils import get_object, shorten_string
from feincms._internal import monkeypatch_method


class TypeRegistryMetaClass(type):
    """
    You can access the list of subclasses as <BaseClass>.types

    TODO use NavigationExtension.__subclasses__() instead?
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'types'):
            cls.types = []
        else:
            cls.types.append(cls)


class PagePretender(object):
    """
    A PagePretender pretends to be a page, but in reality is just a shim layer
    that implements enough functionality to inject fake pages eg. into the
    navigation tree.

    For use as fake navigation page, you should at least define the following
    parameters on creation: title, url, level. If using the translation
    extension, also add language.
    """
    pk = None

    # emulate mptt properties to get the template tags working
    class _mptt_meta:
        level_attr = 'level'

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_absolute_url(self):
        return self.url

    def get_navigation_url(self):
        return self.get_absolute_url()

    def get_level(self):
        return self.level

    def get_children(self):
        """ overwrite this if you want nested extensions using recursetree """
        return []

    def available_translations(self):
        return ()

    def get_original_translation(self, page):
        return page

    def short_title(self):
        return shorten_string(self.title)


class NavigationExtension(six.with_metaclass(TypeRegistryMetaClass)):
    """
    Base class for all navigation extensions.

    The name attribute is shown to the website administrator.
    """

    name = _('navigation extension')

    def children(self, page, **kwargs):
        """
        This is the method which must be overridden in every navigation
        extension.

        It receives the page the extension is attached to, the depth up to
        which the navigation should be resolved, and the current request object
        if it is available.
        """

        raise NotImplementedError


def navigation_extension_choices():
    for ext in NavigationExtension.types:
        if (issubclass(ext, NavigationExtension) and
                ext is not NavigationExtension):
            yield ('%s.%s' % (ext.__module__, ext.__name__), ext.name)


def get_extension_class(extension):
    extension = get_object(extension)
    if isinstance(extension, types.ModuleType):
        return getattr(extension, 'Extension')
    return extension


class Extension(extensions.Extension):
    ident = 'navigation'  # TODO actually use this
    navigation_extensions = None

    @cached_property
    def _extensions(self):
        if self.navigation_extensions is None:
            warnings.warn(
                'Automatic registering of navigation extensions has been'
                ' deprecated. Please inherit the extension and put a list'
                ' of dotted python paths into the navigation_extensions'
                ' class variable.', DeprecationWarning, stacklevel=3)

            return OrderedDict(
                ('%s.%s' % (ext.__module__, ext.__name__), ext)
                for ext in NavigationExtension.types
                if (
                    issubclass(ext, NavigationExtension) and
                    ext is not NavigationExtension))

        else:
            return OrderedDict(
                ('%s.%s' % (ext.__module__, ext.__name__), ext)
                for ext
                in map(get_extension_class, self.navigation_extensions))

    def handle_model(self):
        choices = [
            (path, ext.name) for path, ext in self._extensions.items()]

        self.model.add_to_class(
            'navigation_extension',
            models.CharField(
                _('navigation extension'),
                choices=choices,
                blank=True, null=True, max_length=200,
                help_text=_(
                    'Select the module providing subpages for this page if'
                    ' you need to customize the navigation.')))

        extension = self

        @monkeypatch_method(self.model)
        def extended_navigation(self, **kwargs):
            if not self.navigation_extension:
                return self.children.in_navigation()

            cls = None

            try:
                cls = extension._extensions[self.navigation_extension]
            except KeyError:
                cls = get_object(self.navigation_extension, fail_silently=True)
                extension._extensions[self.navigation_extension] = cls

            if cls:
                return cls().children(self, **kwargs)
            return self.children.in_navigation()

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options(_('Navigation extension'), {
            'fields': ('navigation_extension',),
            'classes': ('collapse',),
        })
