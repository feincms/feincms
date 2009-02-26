import copy

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

import mptt


class TypeRegistryMetaClass(type):
    """
    You can access the list of subclasses as <BaseClass>.types
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'types'):
            cls.types = []
        else:
            cls.types.append(cls)


class Region(models.Model):
    """
    A template region which will be a container for several page contents.

    Often used regions might be "main" and "sidebar"
    """

    title = models.CharField(_('title'), max_length=50, unique=True)
    key = models.CharField(_('key'), max_length=20, unique=True)
    inherited = models.BooleanField(_('inherited'), default=False,
        help_text=_('Should the content be inherited by subpages if they do not define any content for this region?'))

    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')

    def __unicode__(self):
        return self.title


class Template(models.Model):
    """
    A template file on the disk which can be used by pages to render themselves.
    """

    title = models.CharField(max_length=200)
    path = models.CharField(max_length=200)
    regions = models.ManyToManyField(Region, related_name='templates')

    class Meta:
        ordering = ['title']
        verbose_name = _('template')
        verbose_name_plural = _('templates')

    def __unicode__(self):
        return self.title


class ContentProxy(object):
    """
    This proxy offers attribute-style access to the page contents of regions.

    Example:
    >>> page = Page.objects.all()[0]
    >>> page.content.main
    [A list of all page contents which are assigned to the region with key 'main']
    """

    def __init__(self, item, types):
        self.item = item
        self.types = types

    def __getattr__(self, attr):
        """
        Get all item content instances for the specified item and region

        If no item contents could be found for the current item and the region
        has the inherited flag set, this method will go up the ancestor chain
        until either some item contents have found or no ancestors are left.
        """

        try:
            region = self.__dict__['item'].template.regions.get(key=attr)
        except Region.DoesNotExist:
            return []

        def collect_items(item):
            contents = []
            base_field = self.item.__class__.__name__.lower()
            for cls in self.__dict__['types']:
                queryset = getattr(item, '%s_set' % cls.__name__.lower())
                contents += list(queryset.filter(region=region).select_related(
                    base_field, 'region'))

            if not contents and item.parent_id and region.inherited:
                return collect_items(item.parent)

            return contents

        contents = collect_items(self.__dict__['item'])
        contents.sort(key=lambda c: c.ordering)
        return contents


def create_content_base(model):
    class Meta:
        abstract = True
        ordering = ['ordering']

    def __unicode__(self):
        return u'%s on %s, ordering %s' % (self.region, self.parent, self.ordering)

    @classmethod
    def create_content_type(self, model):
        class Meta:
            db_table = '%s_%s' % (self._feincms_parent_model._meta.db_table,
                model.__name__.lower())

        attrs = {
            '__module__': self.__module__,
            'Meta': Meta,
            }

        cls = type(
            model.__name__,
            (self, model,), attrs)
        self.types.append(cls)
        return cls

    def render(self, **kwargs):
        render_fn = getattr(self, 'render_%s' % self.region.key, None)

        if render_fn:
            return render_fn(**kwargs)

        raise NotImplementedError

    attrs = {
        '__module__': model.__module__,
        '__unicode__': __unicode__,
        'create_content_type': create_content_type,
        'render': render,
        'Meta': Meta,
        model.__name__.lower(): models.ForeignKey(model, related_name='%(class)s_set'),
        'region': models.ForeignKey(Region, related_name='%s_%%(class)s_set' % model.__name__.lower()),
        'ordering': models.IntegerField(_('ordering'), default=0),
        '_feincms_parent_model': model,
        'types': [],
        }

    model._feincms_content_model = type(
        '%sContent' % model.__name__,
        (models.Model,), attrs)

    return model._feincms_content_model



