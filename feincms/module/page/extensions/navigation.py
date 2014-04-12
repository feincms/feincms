"""
Extend or modify the navigation with custom entries.

This extension allows the website administrator to select an extension
which processes, modifies or adds subnavigation entries. The bundled
``feincms_nav`` template tag knows how to collect navigation entries,
be they real Page instances or extended navigation entries.
"""

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms.utils import get_object
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
        from feincms.utils import shorten_string
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
        if (issubclass(ext, NavigationExtension)
                and ext is not NavigationExtension):
            yield ('%s.%s' % (ext.__module__, ext.__name__), ext.name)


class Extension(extensions.Extension):
    ident = 'navigation'  # TODO actually use this

    def handle_model(self):
        self.model.add_to_class(
            'navigation_extension',
            models.CharField(
                _('navigation extension'),
                choices=navigation_extension_choices(),
                blank=True, null=True, max_length=200,
                help_text=_(
                    'Select the module providing subpages for this page if'
                    ' you need to customize the navigation.')))

        @monkeypatch_method(self.model)
        def extended_navigation(self, **kwargs):
            if not self.navigation_extension:
                return self.children.in_navigation()

            cls = get_object(self.navigation_extension, fail_silently=True)
            if not cls or not callable(cls):
                return self.children.in_navigation()

            return cls().children(self, **kwargs)

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options(_('Navigation extension'), {
            'fields': ('navigation_extension',),
            'classes': ('collapse',),
        })
