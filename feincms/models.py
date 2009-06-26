import copy

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import Http404
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

import mptt


class Region(object):
    def __init__(self, key, title, *args):
        self.key = key
        self.title = title
        self.inherited = args and args[0]=='inherited'

    def __unicode__(self):
        return unicode(self.title)


class Template(object):
    def __init__(self, title, path, regions, key=None):
        if not key:
            key = path

        self.key = key
        self.title = title
        self.path = path

        def _make_region(data):
            if isinstance(data, Region):
                return data
            return Region(*data)

        self.regions = [_make_region(row) for row in regions]
        self.regions_dict = dict((r.key, r) for r in self.regions)

    def __unicode__(self):
        return unicode(self.title)


class Base(models.Model):
    """
    This is the base class for your CMS models.
    """

    class Meta:
        abstract = True

    @classmethod
    def register_regions(cls, *regions):
        """

        Example:
            BlogEntry.register_regions(
                ('main', _('Main content area')),
                )
        """

        cls.template = Template('', '', regions)

    @classmethod
    def register_templates(cls, *templates):
        """

        Example:
            Page.register_templates({
                'key': 'base',
                'title': _('Standard template'),
                'path': 'feincms_base.html',
                'regions': (
                    ('main', _('Main content area')),
                    ('sidebar', _('Sidebar'), 'inherited'),
                    ),
                }, {
                'key': '2col',
                'title': _('Template with two columns'),
                'path': 'feincms_2col.html',
                'regions': (
                    ('col1', _('Column one')),
                    ('col2', _('Column two')),
                    ('sidebar', _('Sidebar'), 'inherited'),
                    ),
                })
        """

        instances = {}
        choices = []

        for template in templates:
            if not isinstance(template, Template):
                template = Template(**template)

            instances[template.key] = template
            choices.append((template.key, template.title))

        cls.TEMPLATE_CHOICES = choices

        cls.add_to_class('template_key', models.CharField(_('template'), max_length=20,
            choices=cls.TEMPLATE_CHOICES, default=choices[0][0]))

        cls._feincms_templates = instances

        def _template(self):
            return self._feincms_templates[self.template_key]

        cls.template = property(_template)

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
            'SELECT %d, COUNT(id) FROM %s WHERE parent_id=%s AND region=%%s' % (
                idx,
                cls._meta.db_table,
                self.pk) for idx, cls in enumerate(self._feincms_content_types)])

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(sql, [region.key]*len(self._feincms_content_types))

        counts = [row[1] for row in cursor.fetchall()]

        if not any(counts):
            return []

        contents = []
        for idx, cnt in enumerate(counts):
            if cnt:
                contents += list(
                    self._feincms_content_types[idx].objects.filter(
                        parent=self,
                        region=region.key).select_related('parent', 'region'))

        return contents

    @classmethod
    def _create_content_base(cls):
        """
        This is purely an internal method. Here, we create a base class for the
        concrete content types, which are built in `create_content_type`.

        The three fields added to build a concrete content type class/model are
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

        def fe_render(self, **kwargs):
            """
            Frontend Editing enabled renderer
            """

            if 'request' in kwargs:
                request = kwargs['request']

                if request.session and request.session.get('frontend_editing'):
                    return render_to_string('admin/feincms/fe_box.html', {
                        'content': self.render(**kwargs),
                        'identifier': self.fe_identifier(),
                        })

            return self.render(**kwargs)

        def fe_identifier(self):
            return u'%s-%s-%s' % (
                self.__class__.__name__.lower(),
                self.parent_id,
                self.id,
                )

        attrs = {
            '__module__': cls.__module__,
            '__unicode__': __unicode__,
            'render': render,
            'fe_render': fe_render,
            'fe_identifier': fe_identifier,
            'Meta': Meta,
            'parent': models.ForeignKey(cls, related_name='%(class)s_set'),
            'region': models.CharField(max_length=20),
            'ordering': models.IntegerField(_('ordering'), default=0),
            }

        # save reference to base class on CMS class
        cls._feincms_content_model = type('%sContent' % cls.__name__,
            (models.Model,), attrs)

        # list of concrete content types
        cls._feincms_content_types = []

        # list of item editor context processors
        cls.feincms_item_editor_context_processors = []

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

        try:
            getattr(cls, '%s_set' % model.__name__.lower())
            raise ImproperlyConfigured, 'Cannot create content type using %s.%s for %s.%s, because %s_set is already taken.' % (
                model.__module__, model.__name__,
                cls.__module__, cls.__name__,
                model.__name__.lower())
        except AttributeError:
            # everything ok
            pass

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

        if hasattr(model, 'feincms_item_editor_context_processors'):
            cls.feincms_item_editor_context_processors.extend(
                model.feincms_item_editor_context_processors)

        # collect item editor includes from the content type
        if hasattr(model, 'feincms_item_editor_includes'):
            for key, includes in model.feincms_item_editor_includes.items():
                cls.feincms_item_editor_includes.setdefault(key, []).extend(includes)

        return new_type

    def copy_content_from(self, obj):
        for cls in self._feincms_content_models:
            for content in cls.objects.filter(parent=obj):
                data = model_to_dict(content)
                del content['id']
                new = cls(**content)
                new.parent = self
                new.save()


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
            region = item.template.regions_dict[attr]
        except KeyError:
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

