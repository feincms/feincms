"""
This is the core of FeinCMS

All models defined here are abstract, which means no tables are created in
the feincms_ namespace.
"""

import itertools
import warnings

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.db.models.loading import get_model
from django.forms.widgets import Media
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from feincms import settings, ensure_completely_loaded
from feincms.utils import get_object, copy_model_instance

try:
    any
except NameError:
    # For Python 2.4
    from feincms.compat import c_any as any


class Region(object):
    """
    This class represents a region inside a template. Example regions might be
    'main' and 'sidebar'.
    """

    def __init__(self, key, title, *args):
        self.key = key
        self.title = title
        self.inherited = args and args[0] == 'inherited' or False
        self._content_types = []

    def __unicode__(self):
        return force_unicode(self.title)

    @property
    def content_types(self):
        """
        Returns a list of content types registered for this region as a list
        of (content type key, beautified content type name) tuples
        """

        return [(ct.__name__.lower(), ct._meta.verbose_name) for ct in self._content_types]


class Template(object):
    """
    A template is a standard Django template which is used to render a
    CMS object, most commonly a page.
    """

    def __init__(self, title, path, regions, key=None, preview_image=None):
        # The key is what will be stored in the database. If key is undefined
        # use the template path as fallback.
        if not key:
            key = path

        self.key = key
        self.title = title
        self.path = path
        self.preview_image = preview_image

        def _make_region(data):
            if isinstance(data, Region):
                return data
            return Region(*data)

        self.regions = [_make_region(row) for row in regions]
        self.regions_dict = dict((r.key, r) for r in self.regions)

    def __unicode__(self):
        return force_unicode(self.title)


class ContentProxy(object):
    def __init__(self, item):
        item._needs_content_types()

        self.item = item
        self.content_type_instances = self._fetch_content_type_instances(item)
        self.media_cache = None

    def _fetch_content_type_counts(self, item, regions=None):
        tmpl = 'SELECT %d AS ct_idx, COUNT(id) FROM %s WHERE parent_id=%s'
        args = []

        if regions:
            tmpl += ' AND region IN (' + ','.join(['%%s'] * len(regions)) + ')'
            args.extend(regions * len(item._feincms_content_types))

        sql = ' UNION '.join([tmpl % (idx, cls._meta.db_table, item.pk)\
            for idx, cls in enumerate(item._feincms_content_types)])
        sql = 'SELECT * FROM ( ' + sql + ' ) AS ct ORDER BY ct_idx'

        cursor = connection.cursor()
        cursor.execute(sql, args)

        return [row for row in cursor.fetchall() if row[1]]

    def _fetch_content_type_instances(self, item, counts=None):
        def _materialize(item, counts, regions=None):
            contents = {}
            query = Q(parent=item)

            if regions:
                query &= Q(region__in=regions)

            for idx, cnt in counts:
                for instance in item._feincms_content_types[idx].get_queryset(query):
                    contents.setdefault(instance.region, []).append(instance)
            return contents

        if counts is None:
            counts = self._fetch_content_type_counts(item)

        contents = _materialize(item, counts)

        # TODO this only applies to hierarchically organized Base subclasses...
        empty_inherited_regions = set()
        for region in item.template.regions:
            if region.inherited and not contents.get(region.key):
                empty_inherited_regions.add(region.key)

        # TODO performance test this a bit...
        if empty_inherited_regions:
            ancestors = item.get_ancestors(ascending=True)

            for ancestor in ancestors:
                inherited_counts = self._fetch_content_type_counts(ancestor,
                    regions=tuple(empty_inherited_regions))

                if inherited_counts:
                    inherited_contents = _materialize(ancestor, inherited_counts)

                    for region in tuple(empty_inherited_regions):
                        if inherited_contents.get(region):
                            empty_inherited_regions.discard(region)
                            contents[region] = inherited_contents.get(region)

                if not empty_inherited_regions:
                    break

        return dict((region, sorted(instances, key=lambda c: c.ordering))\
            for region, instances in contents.iteritems())

    def all_of_type(self, type):
        return [ct for ct in itertools.chain(*self.content_type_instances.values()) if isinstance(ct, type)]

    def __getattr__(self, attr):
        """
        Get all item content instances for the specified item and region

        If no item contents could be found for the current item and the region
        has the inherited flag set, this method will go up the ancestor chain
        until either some item contents have found or no ancestors are left.
        """
        if (attr.startswith('__')):
            raise AttributeError

        instances = self.__dict__['content_type_instances']
        return instances.get(attr, [])

    def _get_media(self):
        if self.media_cache is None:
            media = Media()

            instances = self.__dict__['content_type_instances']
            for contents in instances.values():
                for content in contents:
                    if hasattr(content, 'media'):
                        media = media + content.media

            self.media_cache = media
        return self.media_cache
    media = property(_get_media)


def create_base_model(inherit_from=models.Model):
    class Base(inherit_from):
        """
        This is the base class for your CMS models.
        """

        content_proxy_class = ContentProxy

        class Meta:
            abstract = True

        _cached_django_content_type = None

        @classmethod
        def register_regions(cls, *regions):
            """
            Register a list of regions. Only use this if you do not want to use
            multiple templates with this model (read: not use ``register_templates``)::

                BlogEntry.register_regions(
                    ('main', _('Main content area')),
                    )
            """

            if hasattr(cls, 'template'):
                warnings.warn(
                    'Ignoring second call to register_regions.',
                    RuntimeWarning)
                return

            # implicitly creates a dummy template object -- the item editor
            # depends on the presence of a template.
            cls.template = Template('', '', regions)
            cls._feincms_all_regions = cls.template.regions

        @classmethod
        def register_templates(cls, *templates):
            """
            Register templates and add a ``template_key`` field to the model for
            saving the selected template::

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

            if not hasattr(cls, '_feincms_templates'):
                cls._feincms_templates = SortedDict()
                cls.TEMPLATES_CHOICES = []

            instances = getattr(cls, '_feincms_templates', SortedDict())

            for template in templates:
                if not isinstance(template, Template):
                    template = Template(**template)

                instances[template.key] = template

            try:
                field = cls._meta.get_field_by_name('template_key')[0]
            except (FieldDoesNotExist, IndexError):
                cls.add_to_class('template_key', models.CharField(_('template'), max_length=255, choices=()))
                field = cls._meta.get_field_by_name('template_key')[0]

                def _template(self):
                    ensure_completely_loaded()

                    try:
                        return self._feincms_templates[self.template_key]
                    except KeyError:
                        # return first template as a fallback if the template
                        # has changed in-between
                        return self._feincms_templates[
                            self._feincms_templates.keys()[0]]

                cls.template = property(_template)

            cls.TEMPLATE_CHOICES = field._choices = [(template.key, template.title)
                for template in cls._feincms_templates.values()]
            field.default = field.choices[0][0]

            # Build a set of all regions used anywhere
            cls._feincms_all_regions = set()
            for template in cls._feincms_templates.values():
                cls._feincms_all_regions.update(template.regions)

        @classmethod
        def register_extension(cls, register_fn):
            """
            Call the register function of an extension. You must override this
            if you provide a custom ModelAdmin class and want your extensions to
            be able to patch stuff in.
            """
            register_fn(cls, None)

        @classmethod
        def register_extensions(cls, *extensions):
            if not hasattr(cls, '_feincms_extensions'):
                cls._feincms_extensions = set()

            here = cls.__module__.split('.')[:-1]
            here_path = '.'.join(here + ['extensions'])
            common_path = '.'.join(here[:-1] + ['extensions'])

            for ext in extensions:
                if ext in cls._feincms_extensions:
                    continue

                if isinstance(ext, basestring):
                    try:
                        fn = get_object(ext + '.register')
                    except ImportError:
                        try:
                            fn = get_object('%s.%s.register' % ( here_path, ext ) )
                        except ImportError:
                            fn = get_object('%s.%s.register' % ( common_path, ext ) )
                # Not a string, so take our chances and just try to access "register"
                else:
                    fn = ext.register

                cls.register_extension(fn)
                cls._feincms_extensions.add(ext)

        @property
        def content(self):
            """
            Provide a simple interface for getting all content blocks for a region.
            """

            if not hasattr(self, '_content_proxy'):
                self._content_proxy = self.content_proxy_class(self)

            return self._content_proxy

        def _get_content_types_for_region(self, region):
            # find all concrete content type tables which have at least one entry for
            # the current CMS object and region
            # This method is overridden by a more efficient implementation if
            # the ct_tracker extension is active.

            from django.core.cache import cache as django_cache

            counts = None
            ck = None
            # ???: Should we move the cache_key() method to Base, so we can avoid
            # the if-it-supports-it dance?
            if settings.FEINCMS_USE_CACHE and getattr(self, 'cache_key', None):
                ck = 'CNT-FOR-REGION-' + region.key + '-' + self.cache_key()
                counts = django_cache.get(ck)

            if counts is None:
                sql = ' UNION '.join([
                    'SELECT %d AS ct_idx, COUNT(id) FROM %s WHERE parent_id=%s AND region=%%s' % (
                        idx,
                        cls._meta.db_table,
                        self.pk) for idx, cls in enumerate(self._feincms_content_types)])
                sql = 'SELECT * FROM ( ' + sql + ' ) AS ct ORDER BY ct_idx'

                from django.db import connection
                cursor = connection.cursor()
                cursor.execute(sql, [region.key] * len(self._feincms_content_types))

                counts = [row[1] for row in cursor.fetchall()]

                if ck:
                    django_cache.set(ck, counts)

            return counts

        def _content_for_region(self, region):
            """
            This method is used primarily by the LegacyContentProxy
            """
            self._needs_content_types()

            counts = self._get_content_types_for_region(region)

            if not any(counts):
                return []

            contents = []
            for idx, cnt in enumerate(counts):
                if cnt:
                    # the queryset is evaluated right here, because the content objects
                    # of different type will have to be sorted into a list according
                    # to their 'ordering' attribute later
                    contents += list(
                        self._feincms_content_types[idx].get_queryset(
                            Q(parent=self) & Q(region=region.key)))

            return contents

        @classmethod
        def _create_content_base(cls):
            """
            This is purely an internal method. Here, we create a base class for the
            concrete content types, which are built in ``create_content_type``.

            The three fields added to build a concrete content type class/model are
            ``parent``, ``region`` and ``ordering``.
            """

            # We need a template, because of the possibility of restricting content types
            # to a subset of all available regions. Each region object carries a list of
            # all allowed content types around. Content types created before a region is
            # initialized would not be available in the respective region; we avoid this
            # problem by raising an ImproperlyConfigured exception early.
            cls._needs_templates()

            class Meta:
                abstract = True
                app_label = cls._meta.app_label
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

                render_fn = getattr(self, 'render_%s' % self.region, None)

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
                """
                Returns an identifier which is understood by the frontend editing
                javascript code. (It is used to find the URL which should be used
                to load the form for every given block of content.)
                """

                return u'%s-%s-%s-%s-%s' % (
                    cls._meta.app_label,
                    cls._meta.module_name,
                    self.__class__.__name__.lower(),
                    self.parent_id,
                    self.id,
                    )

            def get_queryset(cls, filter_args):
                return cls.objects.select_related().filter(filter_args)

            attrs = {
                '__module__': cls.__module__, # The basic content type is put into
                                              # the same module as the CMS base type.
                                              # If an app_label is not given, Django
                                              # needs to know where a model comes
                                              # from, therefore we ensure that the
                                              # module is always known.
                '__unicode__': __unicode__,
                'render': render,
                'fe_render': fe_render,
                'fe_identifier': fe_identifier,
                'get_queryset': classmethod(get_queryset),
                'Meta': Meta,
                'parent': models.ForeignKey(cls, related_name='%(class)s_set'),
                'region': models.CharField(max_length=255),
                'ordering': models.IntegerField(_('ordering'), default=0),
                }

            # create content base type and save reference on CMS class
            cls._feincms_content_model = type('%sContent' % cls.__name__,
                (models.Model,), attrs)

            # list of concrete content types
            cls._feincms_content_types = []

            # list of concrete content types having methods which may be called
            # before or after rendering the content:
            #
            # def process(self, request):
            #     May return a response early to short-circuit the request-response cycle
            #
            # def finalize(self, request, response)
            #     May modify the response or replace it entirely by returning a new one
            #
            cls._feincms_content_types_with_process = []
            cls._feincms_content_types_with_finalize = []

            # list of item editor context processors, will be extended by content types
            if hasattr(cls, 'feincms_item_editor_context_processors'):
                cls.feincms_item_editor_context_processors = list(cls.feincms_item_editor_context_processors)
            else:
                cls.feincms_item_editor_context_processors = []

            # list of templates which should be included in the item editor, will be extended
            # by content types
            if hasattr(cls, 'feincms_item_editor_includes'):
                cls.feincms_item_editor_includes = dict(cls.feincms_item_editor_includes)
            else:
                cls.feincms_item_editor_includes = {}

        @classmethod
        def create_content_type(cls, model, regions=None, class_name=None, **kwargs):
            """
            This is the method you'll use to create concrete content types.

            If the CMS base class is ``page.models.Page``, its database table will be
            ``page_page``. A concrete content type which is created from ``ImageContent``
            will use ``page_page_imagecontent`` as its table.

            If you want a content type only available in a subset of regions, you can
            pass a list/tuple of region keys as ``regions``. The content type will only
            appear in the corresponding tabs in the item editor.

            You can pass additional keyword arguments to this factory function. These
            keyword arguments will be passed on to the concrete content type, provided
            that it has a ``initialize_type`` classmethod. This is used f.e. in
            ``MediaFileContent`` to pass a set of possible media positions (f.e. left,
            right, centered) through to the content type.
            """

            if not class_name:
                class_name = model.__name__

            # prevent double registration and registration of two different content types
            # with the same class name because of related_name clashes
            try:
                getattr(cls, '%s_set' % class_name.lower())
                warnings.warn(
                    'Cannot create content type using %s.%s for %s.%s, because %s_set is already taken.' % (
                        model.__module__, class_name,
                        cls.__module__, cls.__name__,
                        class_name.lower()),
                    RuntimeWarning)
                return
            except AttributeError:
                # everything ok
                pass

            # Next name clash test. Happens when the same content type is created
            # for two Base subclasses living in the same Django application
            # (github issues #73 and #150)
            other_model = get_model(cls._meta.app_label, class_name)
            if other_model:
                warnings.warn(
                    'It seems that the content type %s exists twice in %s. Use the class_name argument to create_content_type to avoid this error.' % (
                        model.__name__,
                        cls._meta.app_label),
                    RuntimeWarning)

            if not model._meta.abstract:
                raise ImproperlyConfigured, 'Cannot create content type from non-abstract model (yet).'

            if not hasattr(cls, '_feincms_content_model'):
                cls._create_content_base()

            feincms_content_base = cls._feincms_content_model

            class Meta(feincms_content_base.Meta):
                db_table = '%s_%s' % (cls._meta.db_table, class_name.lower())
                verbose_name = model._meta.verbose_name
                verbose_name_plural = model._meta.verbose_name_plural

            attrs = {
                '__module__': cls.__module__, # put the concrete content type into the
                                              # same module as the CMS base type; this is
                                              # necessary because 1. Django needs to know
                                              # the module where a model lives and 2. a
                                              # content type may be used by several CMS
                                              # base models at the same time (f.e. in
                                              # the blog and the page module).
                'Meta': Meta,
                }

            new_type = type(
                class_name,
                (model, feincms_content_base,),
                attrs)
            cls._feincms_content_types.append(new_type)

            if hasattr(getattr(new_type, 'process', None), '__call__'):
                cls._feincms_content_types_with_process.append(new_type)
            if hasattr(getattr(new_type, 'finalize', None), '__call__'):
                cls._feincms_content_types_with_finalize.append(new_type)

            # content types can be limited to a subset of regions
            if not regions:
                regions = set([region.key for region in cls._feincms_all_regions])

            for region in cls._feincms_all_regions:
                if region.key in regions:
                    region._content_types.append(new_type)

            # Add a list of CMS base types for which a concrete content type has
            # been created to the abstract content type. This is needed f.e. for the
            # update_rsscontent management command, which needs to find all concrete
            # RSSContent types, so that the RSS feeds can be fetched
            if not hasattr(model, '_feincms_content_models'):
                model._feincms_content_models = []

            model._feincms_content_models.append(new_type)

            # Add a backlink from content-type to content holder class
            new_type._feincms_content_class = cls

            # Handle optgroup argument for grouping content types in the item editor
            optgroup = kwargs.pop('optgroup', None)
            if optgroup:
                new_type.optgroup = optgroup

            # customization hook.
            if hasattr(new_type, 'initialize_type'):
                new_type.initialize_type(**kwargs)
            else:
                for k, v in kwargs.items():
                    setattr(new_type, k, v)

            # collect item editor context processors from the content type
            if hasattr(model, 'feincms_item_editor_context_processors'):
                cls.feincms_item_editor_context_processors.extend(
                    model.feincms_item_editor_context_processors)

            # collect item editor includes from the content type
            if hasattr(model, 'feincms_item_editor_includes'):
                for key, includes in model.feincms_item_editor_includes.items():
                    cls.feincms_item_editor_includes.setdefault(key, set()).update(includes)

            # Ensure meta information concerning related fields is up-to-date.
            #
            # Upon accessing the related fields information from Model._meta, the related
            # fields are cached and never refreshed again (because models and model relations
            # are defined upon import time, if you do not fumble around with models like we
            # do right here.)
            #
            # Adding related models after this information has been cached leads to models
            # not knowing about related items, which again causes the bug we had in
            # issue #63 on github:
            #
            # http://github.com/matthiask/feincms/issues/issue/63/
            #
            # Currently, all methods filling up the Model.meta cache start with fill_.
            # We call all these methods upon creation of a new content type to make sure
            # that we really really do not forget a relation somewhere. Of course, we do
            # too much here, but better a bit too much upon application startup than not
            # enough like before.
            for fn in [s for s in dir(cls._meta) if s[:6]=='_fill_']:
                getattr(cls._meta, fn)()

            return new_type

        @property
        def _django_content_type(self):
            if getattr(self.__class__, '_cached_django_content_type', None) is None:
                self.__class__._cached_django_content_type = ContentType.objects.get_for_model(self)
            return self.__class__._cached_django_content_type

        @classmethod
        def content_type_for(cls, model):
            """
            Return the concrete content type for an abstract content type::

                from feincms.content.video.models import VideoContent
                concrete_type = Page.content_type_for(VideoContent)
            """

            if not hasattr(cls, '_feincms_content_types') or not cls._feincms_content_types:
                return None

            for type in cls._feincms_content_types:
                if issubclass(type, model):
                    return type
            return None

        @classmethod
        def _needs_templates(cls):
            # helper which can be used to ensure that either register_regions or
            # register_templates has been executed before proceeding
            if not hasattr(cls, 'template'):
                raise ImproperlyConfigured, 'You need to register at least one template or one region on %s.' % (
                    cls.__name__,
                    )

        @classmethod
        def _needs_content_types(cls):
            # Check whether any content types have been created for this base class
            if not hasattr(cls, '_feincms_content_types') or not cls._feincms_content_types:
                raise ImproperlyConfigured, 'You need to create at least one content type for the %s model.' % (cls.__name__)

        def copy_content_from(self, obj):
            """
            Copy all content blocks over to another CMS base object. (Must be of the
            same type, but this is not enforced. It will crash if you try to copy content
            from another CMS base type.)
            """

            for cls in self._feincms_content_types:
                for content in cls.objects.filter(parent=obj):
                    new = copy_model_instance(content, exclude=('id', 'parent'))
                    new.parent = self
                    new.save()

        def replace_content_with(self, obj):
            for cls in self._feincms_content_types:
                cls.objects.filter(parent=self).delete()
            self.copy_content_from(obj)

    return Base

# Legacy support
Base = create_base_model()
