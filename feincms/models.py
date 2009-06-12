import copy

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
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

    title = models.CharField(_('title'), max_length=200)
    path = models.CharField(_('path'), max_length=200)
    regions = models.ManyToManyField(Region, related_name='templates',
        verbose_name=_('regions'))

    class Meta:
        ordering = ['title']
        verbose_name = _('template')
        verbose_name_plural = _('templates')

    def __unicode__(self):
        return self.title


def first_template():
    try:
        return Template.objects.all()[0]
    except IndexError:
        return None


class Base(models.Model):
    """
    This is the base class for your CMS models.
    """

    template = models.ForeignKey(Template, default=first_template,
        verbose_name=_('template'))

    class Meta:
        abstract = True

    @property
    def content(self):
        """
        Provide a simple interface for getting all content blocks for a region.
        """

        if not hasattr(self, '_content_proxy'):
            self._content_proxy = ContentProxy(self)

        return self._content_proxy

    def _content_for_region(self, region):
        """
        This method is used primarily by the ContentProxy
        """

        if not hasattr(self, '_feincms_content_types') or not self._feincms_content_types:
            raise ImproperlyConfigured, 'You need to create at least one content type for the %s model.' % (self.__class__.__name__)

        # find all concrete content type tables which have at least one entry for
        # the current CMS object and region
        sql = ' UNION '.join([
            'SELECT %d, COUNT(id) FROM %s WHERE parent_id=%s AND region_id=%s' % (
                idx,
                cls._meta.db_table,
                self.pk,
                region.id) for idx, cls in enumerate(self._feincms_content_types)])

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(sql)

        counts = [row[1] for row in cursor.fetchall()]

        if not any(counts):
            return []

        contents = []
        for idx, cnt in enumerate(counts):
            if cnt:
                contents += list(
                    self._feincms_content_types[idx].objects.filter(
                        parent=self,
                        region=region).select_related('parent', 'region'))

        return contents

    @classmethod
    def _create_content_base(cls):
        """
        This is purely an internal method. Here, we create a base class for the
        concrete content types, which are built in `create_content_type`.

        The three fields added to build a concrete content type class/mdoel are
        `parent`, `region` and `ordering`.
        """

        class Meta:
            abstract = True
            ordering = ['ordering']

        def __unicode__(self):
            return u'%s on %s, ordering %s' % (self.region, self.parent, self.ordering)

        def render(self, **kwargs):
            """
            Default render implementation, tries to call a method named after the
            region key before giving up.

            You'll probably override the render method itself most of the time
            instead of adding region-specific render methods.
            """

            render_fn = getattr(self, 'render_%s' % self.region.key, None)

            if render_fn:
                return render_fn(**kwargs)

            raise NotImplementedError

        attrs = {
            '__module__': cls.__module__,
            '__unicode__': __unicode__,
            'render': render,
            'Meta': Meta,
            'parent': models.ForeignKey(cls, related_name='%(class)s_set'),
            'region': models.ForeignKey(Region, related_name='%s_%%(class)s_set' % cls.__name__.lower()),
            'ordering': models.IntegerField(_('ordering'), default=0),
            }

        # save reference to base class on CMS class
        cls._feincms_content_model = type('%sContent' % cls.__name__,
            (models.Model,), attrs)

        # list of concrete content types
        cls._feincms_content_types = []

        # list of templates which should be included in the item editor
        cls.feincms_item_editor_includes = {}

    @classmethod
    def create_content_type(cls, model, **kwargs):
        """
        This is the method you'll use to create concrete content types.

        If the CMS base class is `page.models.Page`, its database table will be
        `page_page`. A concrete content type which is created from `ImageContent`
        will use `page_page_imagecontent` as its table.

        You can pass additional keyword arguments to this factory function. These
        keyword arguments will be passed on to the concrete content type, provided
        that it has a `handle_kwargs` classmethod. This is used f.e. in
        `MediaFileContent` to pass a set of possible media positions (f.e. left,
        right, centered) through to the content type.
        """

        if not hasattr(cls, '_feincms_content_model'):
            cls._create_content_base()

        feincms_content_base = getattr(cls, '_feincms_content_model')

        class Meta:
            db_table = '%s_%s' % (cls._meta.db_table, model.__name__.lower())
            verbose_name = model._meta.verbose_name
            verbose_name_plural = model._meta.verbose_name_plural

        attrs = {
            '__module__': cls.__module__, # put the concrete content type into the
                                          # same module as the CMS base type
            'Meta': Meta,
            }

        new_type = type(
            model.__name__,
            (model, feincms_content_base,),
            attrs)
        cls._feincms_content_types.append(new_type)

        # Add a list of CMS base types for which a concrete content type has
        # been created to the abstract content type. This is needed f.e. for the
        # update_rsscontent management command, which needs to find all concrete
        # RSSContent types, so that the RSS feeds can be fetched
        if not hasattr(model, '_feincms_content_models'):
            model._feincms_content_models = []

        model._feincms_content_models.append(new_type)

        # customization hook.
        if hasattr(new_type, 'handle_kwargs'):
            new_type.handle_kwargs(**kwargs)
        else:
            for k, v in kwargs.items():
                setattr(new_type, k, v)

        # collect item editor includes from the content type
        if hasattr(model, 'feincms_item_editor_includes'):
            for key, includes in model.feincms_item_editor_includes.items():
                cls.feincms_item_editor_includes.setdefault(key, []).extend(includes)

        return new_type


class ContentProxy(object):
    """
    This proxy offers attribute-style access to the page contents of regions.

    Example:
    >>> page = Page.objects.all()[0]
    >>> page.content.main
    [A list of all page contents which are assigned to the region with key 'main']
    """

    def __init__(self, item):
        self.item = item

    def __getattr__(self, attr):
        """
        Get all item content instances for the specified item and region

        If no item contents could be found for the current item and the region
        has the inherited flag set, this method will go up the ancestor chain
        until either some item contents have found or no ancestors are left.
        """

        item = self.__dict__['item']

        try:
            region = item.template.regions.get(key=attr)
        except Region.DoesNotExist:
            return []

        def collect_items(obj):
            contents = obj._content_for_region(region)

            # go to parent if this model has a parent attribute
            # TODO this should be abstracted into a property/method or something
            # The link which should be followed is not always '.parent'
            if not contents and hasattr(obj, 'parent_id') and obj.parent_id and region.inherited:
                return collect_items(obj.parent)

            return contents

        contents = collect_items(item)
        contents.sort(key=lambda c: c.ordering)
        return contents

