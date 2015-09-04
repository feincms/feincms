"""
This is the core of FeinCMS

All models defined here are abstract, which means no tables are created in
the feincms\_ namespace.
"""

from __future__ import absolute_import, unicode_literals

from collections import OrderedDict
from functools import reduce
import sys
import operator
import warnings

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, models
from django.db.models import Q
from django.forms.widgets import Media
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from feincms import ensure_completely_loaded
from feincms.extensions import ExtensionsMixin
from feincms.utils import copy_model_instance


@python_2_unicode_compatible
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

    def __str__(self):
        return force_text(self.title)

    @property
    def content_types(self):
        """
        Returns a list of content types registered for this region as a list
        of (content type key, beautified content type name) tuples
        """

        return [
            (ct.__name__.lower(), ct._meta.verbose_name)
            for ct in self._content_types
        ]


@python_2_unicode_compatible
class Template(object):
    """
    A template is a standard Django template which is used to render a
    CMS object, most commonly a page.
    """

    def __init__(self, title, path, regions, key=None, preview_image=None,
                 **kwargs):
        # The key is what will be stored in the database. If key is undefined
        # use the template path as fallback.
        if not key:
            key = path

        self.key = key
        self.title = title
        self.path = path
        self.preview_image = preview_image
        self.singleton = kwargs.get('singleton', False)
        self.child_template = kwargs.get('child_template', None)
        self.enforce_leaf = kwargs.get('enforce_leaf', False)
        self.urlconf = kwargs.get('urlconf', None)

        def _make_region(data):
            if isinstance(data, Region):
                return data
            return Region(*data)

        self.regions = [_make_region(row) for row in regions]
        self.regions_dict = dict((r.key, r) for r in self.regions)

    def __str__(self):
        return force_text(self.title)


class ContentProxy(object):
    """
    The ``ContentProxy`` is responsible for loading the content blocks for all
    regions (including content blocks in inherited regions) and assembling
    media definitions.

    The content inside a region can be fetched using attribute access with
    the region key. This is achieved through a custom ``__getattr__``
    implementation.
    """

    def __init__(self, item):
        item._needs_content_types()
        self.item = item
        self.db = item._state.db
        self._cache = {
            'cts': {},
        }

    def _inherit_from(self):
        """
        Returns a list of item primary keys to try inheriting content from if
        a certain region is empty.

        Returns an ascending list of ancestors (using MPTT) by default. This
        is good enough (tm) for pages.
        """

        return self.item.get_ancestors(ascending=True).values_list(
            'pk', flat=True)

    def _fetch_content_type_counts(self):
        """
        Returns a structure describing which content types exist for the object
        with the given primary key.

        The structure is as follows, where pk is the passed primary key and
        ct_idx are indices into the item._feincms_content_types list:

            {
                'region_key': [
                    (pk, ct_idx1),
                    (pk, ct_idx2),
                    ],
                ...
            }
        """

        if 'counts' not in self._cache:
            counts = self._fetch_content_type_count_helper(self.item.pk)

            empty_inherited_regions = set()
            for region in self.item.template.regions:
                if region.inherited and not counts.get(region.key):
                    empty_inherited_regions.add(region.key)

            if empty_inherited_regions:
                for parent in self._inherit_from():
                    parent_counts = self._fetch_content_type_count_helper(
                        parent, regions=tuple(empty_inherited_regions))

                    counts.update(parent_counts)
                    for key in parent_counts.keys():
                        empty_inherited_regions.discard(key)

                    if not empty_inherited_regions:
                        break

            self._cache['counts'] = counts
        return self._cache['counts']

    def _fetch_content_type_count_helper(self, pk, regions=None):
        tmpl = [
            'SELECT %d AS ct_idx, region, COUNT(id) FROM %s WHERE parent_id=%s'
        ]
        args = []

        if regions:
            tmpl.append(
                'AND region IN (' + ','.join(['%%s'] * len(regions)) + ')')
            args.extend(regions * len(self.item._feincms_content_types))

        tmpl.append('GROUP BY region')
        tmpl = ' '.join(tmpl)

        sql = ' UNION '.join([
            tmpl % (idx, cls._meta.db_table, pk)
            for idx, cls in enumerate(self.item._feincms_content_types)
        ])
        sql = 'SELECT * FROM ( ' + sql + ' ) AS ct ORDER BY ct_idx'

        cursor = connections[self.db].cursor()
        cursor.execute(sql, args)

        _c = {}
        for ct_idx, region, count in cursor.fetchall():
            if count:
                _c.setdefault(region, []).append((pk, ct_idx))

        return _c

    def _populate_content_type_caches(self, types):
        """
        Populate internal caches for all content types passed
        """

        counts_by_type = {}
        for region, counts in self._fetch_content_type_counts().items():
            for pk, ct_idx in counts:
                counts_by_type.setdefault(
                    self.item._feincms_content_types[ct_idx],
                    [],
                ).append((region, pk))

        # Resolve abstract to concrete content types
        content_types = (
            cls for cls in self.item._feincms_content_types
            if issubclass(cls, tuple(types))
        )

        for cls in content_types:
            counts = counts_by_type.get(cls)
            if cls not in self._cache['cts']:
                if counts:
                    self._cache['cts'][cls] = list(cls.get_queryset(reduce(
                        operator.or_,
                        (Q(region=r[0], parent=r[1]) for r in counts)
                    )))
                else:
                    self._cache['cts'][cls] = []

        # share this content proxy object between all content items
        # so that each can use obj.parent.content to determine its
        # relationship to its siblings, etc.
        for cls, objects in self._cache['cts'].items():
            for obj in objects:
                setattr(obj.parent, '_content_proxy', self)

    def _fetch_regions(self):
        """
        Fetches all content types and group content types into regions
        """

        if 'regions' not in self._cache:
            self._populate_content_type_caches(
                self.item._feincms_content_types)
            contents = {}
            for cls, content_list in self._cache['cts'].items():
                for instance in content_list:
                    contents.setdefault(instance.region, []).append(instance)

            self._cache['regions'] = dict(
                (
                    region,
                    sorted(instances, key=lambda c: c.ordering),
                ) for region, instances in contents.items()
            )

        return self._cache['regions']

    def all_of_type(self, type_or_tuple):
        """
        Returns all content type instances belonging to the type or types
        passed.  If you want to filter for several types at the same time, type
        must be a tuple.

        The content type instances are sorted by their ``ordering`` value,
        but that isn't necessarily meaningful if the same content type exists
        in different regions.
        """

        content_list = []
        if not hasattr(type_or_tuple, '__iter__'):
            type_or_tuple = (type_or_tuple,)
        self._populate_content_type_caches(type_or_tuple)

        for type, contents in self._cache['cts'].items():
            if any(issubclass(type, t) for t in type_or_tuple):
                content_list.extend(contents)

        return sorted(content_list, key=lambda c: c.ordering)

    def _get_media(self):
        """
        Collect the media files of all content types of the current object
        """

        if 'media' not in self._cache:
            media = Media()

            for contents in self._fetch_regions().values():
                for content in contents:
                    if hasattr(content, 'media'):
                        media = media + content.media

            self._cache['media'] = media
        return self._cache['media']
    media = property(_get_media)

    def __getattr__(self, attr):
        """
        Get all item content instances for the specified item and region

        If no item contents could be found for the current item and the region
        has the inherited flag set, this method will go up the ancestor chain
        until either some item contents have found or no ancestors are left.
        """
        if (attr.startswith('__')):
            raise AttributeError

        # Do not trigger loading of real content type models if not necessary
        if not self._fetch_content_type_counts().get(attr):
            return []

        return self._fetch_regions().get(attr, [])


def create_base_model(inherit_from=models.Model):
    """
    This method can  be used to create a FeinCMS base model inheriting from
    your own custom subclass (f.e. extend ``MPTTModel``). The default is to
    extend :class:`django.db.models.Model`.
    """

    class Base(inherit_from, ExtensionsMixin):
        """
        This is the base class for your CMS models. It knows how to create and
        manage content types.
        """

        class Meta:
            abstract = True

        _cached_django_content_type = None

        @classmethod
        def register_regions(cls, *regions):
            """
            Register a list of regions. Only use this if you do not want to use
            multiple templates with this model (read: not use
            ``register_templates``)::

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
            Register templates and add a ``template_key`` field to the model
            for saving the selected template::

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
                cls._feincms_templates = OrderedDict()
                cls.TEMPLATES_CHOICES = []

            instances = cls._feincms_templates

            for template in templates:
                if not isinstance(template, Template):
                    template = Template(**template)

                instances[template.key] = template

            try:
                field = next(iter(
                    field for field in cls._meta.local_fields
                    if field.name == 'template_key'))
            except (StopIteration,):
                cls.add_to_class(
                    'template_key',
                    models.CharField(_('template'), max_length=255, choices=())
                )
                field = next(iter(
                    field for field in cls._meta.local_fields
                    if field.name == 'template_key'))

                def _template(self):
                    ensure_completely_loaded()

                    try:
                        return self._feincms_templates[self.template_key]
                    except KeyError:
                        # return first template as a fallback if the template
                        # has changed in-between
                        return self._feincms_templates[
                            list(self._feincms_templates.keys())[0]]

                cls.template = property(_template)

            cls.TEMPLATE_CHOICES = field._choices = [
                (template_.key, template_.title,)
                for template_ in cls._feincms_templates.values()
            ]
            field.default = field.choices[0][0]

            # Build a set of all regions used anywhere
            cls._feincms_all_regions = set()
            for template in cls._feincms_templates.values():
                cls._feincms_all_regions.update(template.regions)

        #: ``ContentProxy`` class this object uses to collect content blocks
        content_proxy_class = ContentProxy

        @property
        def content(self):
            """
            Instantiate and return a ``ContentProxy``. You can use your own
            custom ``ContentProxy`` by assigning a different class to the
            ``content_proxy_class`` member variable.
            """

            if not hasattr(self, '_content_proxy'):
                self._content_proxy = self.content_proxy_class(self)

            return self._content_proxy

        @classmethod
        def _create_content_base(cls):
            """
            This is purely an internal method. Here, we create a base class for
            the concrete content types, which are built in
            ``create_content_type``.

            The three fields added to build a concrete content type class/model
            are ``parent``, ``region`` and ``ordering``.
            """

            # We need a template, because of the possibility of restricting
            # content types to a subset of all available regions. Each region
            # object carries a list of all allowed content types around.
            # Content types created before a region is initialized would not be
            # available in the respective region; we avoid this problem by
            # raising an ImproperlyConfigured exception early.
            cls._needs_templates()

            class Meta:
                abstract = True
                app_label = cls._meta.app_label
                ordering = ['ordering']

            def __str__(self):
                return (
                    '%s<pk=%s, parent=%s<pk=%s, %s>, region=%s,'
                    ' ordering=%d>') % (
                    self.__class__.__name__,
                    self.pk,
                    self.parent.__class__.__name__,
                    self.parent.pk,
                    self.parent,
                    self.region,
                    self.ordering)

            def render(self, **kwargs):
                """
                Default render implementation, tries to call a method named
                after the region key before giving up.

                You'll probably override the render method itself most of the
                time instead of adding region-specific render methods.
                """

                render_fn = getattr(self, 'render_%s' % self.region, None)

                if render_fn:
                    return render_fn(**kwargs)

                raise NotImplementedError

            def get_queryset(cls, filter_args):
                return cls.objects.select_related().filter(filter_args)

            attrs = {
                # The basic content type is put into
                # the same module as the CMS base type.
                # If an app_label is not given, Django
                # needs to know where a model comes
                # from, therefore we ensure that the
                # module is always known.
                '__module__': cls.__module__,
                '__str__': __str__,
                'render': render,
                'get_queryset': classmethod(get_queryset),
                'Meta': Meta,
                'parent': models.ForeignKey(cls, related_name='%(class)s_set'),
                'region': models.CharField(max_length=255),
                'ordering': models.IntegerField(_('ordering'), default=0),
            }

            # create content base type and save reference on CMS class

            name = '_Internal%sContentTypeBase' % cls.__name__
            if hasattr(sys.modules[cls.__module__], name):
                warnings.warn(
                    'The class %s.%s has the same name as the class that '
                    'FeinCMS auto-generates based on %s.%s. To avoid database'
                    'errors and import clashes, rename one of these classes.'
                    % (cls.__module__, name, cls.__module__, cls.__name__),
                    RuntimeWarning)

            cls._feincms_content_model = python_2_unicode_compatible(
                type(str(name), (models.Model,), attrs))

            # list of concrete content types
            cls._feincms_content_types = []

            # list of concrete content types having methods which may be called
            # before or after rendering the content:
            #
            # def process(self, request, **kwargs):
            #     May return a response early to short-circuit the
            #     request-response cycle
            #
            # def finalize(self, request, response)
            #     May modify the response or replace it entirely by returning
            #     a new one
            #
            cls._feincms_content_types_with_process = []
            cls._feincms_content_types_with_finalize = []

            # list of item editor context processors, will be extended by
            # content types
            if hasattr(cls, 'feincms_item_editor_context_processors'):
                cls.feincms_item_editor_context_processors = list(
                    cls.feincms_item_editor_context_processors)
            else:
                cls.feincms_item_editor_context_processors = []

            # list of templates which should be included in the item editor,
            # will be extended by content types
            if hasattr(cls, 'feincms_item_editor_includes'):
                cls.feincms_item_editor_includes = dict(
                    cls.feincms_item_editor_includes)
            else:
                cls.feincms_item_editor_includes = {}

        @classmethod
        def create_content_type(cls, model, regions=None, class_name=None,
                                **kwargs):
            """
            This is the method you'll use to create concrete content types.

            If the CMS base class is ``page.models.Page``, its database table
            will be ``page_page``. A concrete content type which is created
            from ``ImageContent`` will use ``page_page_imagecontent`` as its
            table.

            If you want a content type only available in a subset of regions,
            you can pass a list/tuple of region keys as ``regions``. The
            content type will only appear in the corresponding tabs in the item
            editor.

            If you use two content types with the same name in the same module,
            name clashes will happen and the content type created first will
            shadow all subsequent content types. You can work around it by
            specifying the content type class name using the ``class_name``
            argument. Please note that this will have an effect on the entries
            in ``django_content_type``, on ``related_name`` and on the table
            name used and should therefore not be changed after running
            ``syncdb`` for the first time.

            Name clashes will also happen if a content type has defined a
            relationship and you try to register that content type to more than
            one Base model (in different modules).  Django will raise an error
            when it tries to create the backward relationship. The solution to
            that problem is, as shown above, to specify the content type class
            name with the ``class_name`` argument.

            If you register a content type to more than one Base class, it is
            recommended to always specify a ``class_name`` when registering it
            a second time.

            You can pass additional keyword arguments to this factory function.
            These keyword arguments will be passed on to the concrete content
            type, provided that it has a ``initialize_type`` classmethod. This
            is used f.e. in ``MediaFileContent`` to pass a set of possible
            media positions (f.e. left, right, centered) through to the content
            type.
            """

            if not class_name:
                class_name = model.__name__

            # prevent double registration and registration of two different
            # content types with the same class name because of related_name
            # clashes
            try:
                getattr(cls, '%s_set' % class_name.lower())
                warnings.warn(
                    'Cannot create content type using %s.%s for %s.%s,'
                    ' because %s_set is already taken.' % (
                        model.__module__, class_name,
                        cls.__module__, cls.__name__,
                        class_name.lower()),
                    RuntimeWarning)
                return
            except AttributeError:
                # everything ok
                pass

            if not model._meta.abstract:
                raise ImproperlyConfigured(
                    'Cannot create content type from'
                    ' non-abstract model (yet).')

            if not hasattr(cls, '_feincms_content_model'):
                cls._create_content_base()

            feincms_content_base = cls._feincms_content_model

            class Meta(feincms_content_base.Meta):
                db_table = '%s_%s' % (cls._meta.db_table, class_name.lower())
                verbose_name = model._meta.verbose_name
                verbose_name_plural = model._meta.verbose_name_plural
                permissions = model._meta.permissions

            attrs = {
                # put the concrete content type into the
                # same module as the CMS base type; this is
                # necessary because 1. Django needs to know
                # the module where a model lives and 2. a
                # content type may be used by several CMS
                # base models at the same time (f.e. in
                # the blog and the page module).
                '__module__': cls.__module__,
                'Meta': Meta,
            }

            new_type = type(
                str(class_name),
                (model, feincms_content_base,),
                attrs,
            )
            cls._feincms_content_types.append(new_type)

            if hasattr(getattr(new_type, 'process', None), '__call__'):
                cls._feincms_content_types_with_process.append(new_type)
            if hasattr(getattr(new_type, 'finalize', None), '__call__'):
                cls._feincms_content_types_with_finalize.append(new_type)

            # content types can be limited to a subset of regions
            if not regions:
                regions = set([
                    region.key for region in cls._feincms_all_regions])

            for region in cls._feincms_all_regions:
                if region.key in regions:
                    region._content_types.append(new_type)

            # Add a list of CMS base types for which a concrete content type
            # has been created to the abstract content type. This is needed
            # f.e. for the update_rsscontent management command, which needs to
            # find all concrete RSSContent types, so that the RSS feeds can be
            # fetched
            if not hasattr(model, '_feincms_content_models'):
                model._feincms_content_models = []

            model._feincms_content_models.append(new_type)

            # Add a backlink from content-type to content holder class
            new_type._feincms_content_class = cls

            # Handle optgroup argument for grouping content types in the item
            # editor
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
                for key, incls in model.feincms_item_editor_includes.items():
                    cls.feincms_item_editor_includes.setdefault(
                        key, set()).update(incls)

            ensure_completely_loaded(force=True)
            return new_type

        @property
        def _django_content_type(self):
            if not getattr(self, '_cached_django_content_type', None):
                self.__class__._cached_django_content_type = (
                    ContentType.objects.get_for_model(self))
            return self.__class__._cached_django_content_type

        @classmethod
        def content_type_for(cls, model):
            """
            Return the concrete content type for an abstract content type::

                from feincms.content.video.models import VideoContent
                concrete_type = Page.content_type_for(VideoContent)
            """

            if (not hasattr(cls, '_feincms_content_types') or
                    not cls._feincms_content_types):
                return None

            for type in cls._feincms_content_types:
                if issubclass(type, model):
                    if type.__base__ is model:
                        return type
            return None

        @classmethod
        def _needs_templates(cls):
            ensure_completely_loaded()

            # helper which can be used to ensure that either register_regions
            # or register_templates has been executed before proceeding
            if not hasattr(cls, 'template'):
                raise ImproperlyConfigured(
                    'You need to register at least one'
                    ' template or one region on %s.' % cls.__name__)

        @classmethod
        def _needs_content_types(cls):
            ensure_completely_loaded()

            # Check whether any content types have been created for this base
            # class
            if not getattr(cls, '_feincms_content_types', None):
                raise ImproperlyConfigured(
                    'You need to create at least one'
                    ' content type for the %s model.' % cls.__name__)

        def copy_content_from(self, obj):
            """
            Copy all content blocks over to another CMS base object. (Must be
            of the same type, but this is not enforced. It will crash if you
            try to copy content from another CMS base type.)
            """

            for cls in self._feincms_content_types:
                for content in cls.objects.filter(parent=obj):
                    new = copy_model_instance(
                        content, exclude=('id', 'parent'))
                    new.parent = self
                    new.save()

        def replace_content_with(self, obj):
            """
            Replace the content of the current object with content of another.

            Deletes all content blocks and calls ``copy_content_from``
            afterwards.
            """

            for cls in self._feincms_content_types:
                cls.objects.filter(parent=self).delete()
            self.copy_content_from(obj)

        @classmethod
        def register_with_reversion(cls):
            try:
                import reversion
            except ImportError:
                raise EnvironmentError("django-reversion is not installed")

            follow = []
            for content_type in cls._feincms_content_types:
                follow.append('%s_set' % content_type.__name__.lower())
                reversion.register(content_type)
            reversion.register(cls, follow=follow)

    return Base


# Legacy support
Base = create_base_model()
