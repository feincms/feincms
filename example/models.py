from django import forms
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel

from feincms.module.blog.models import Entry, EntryAdmin
from feincms.module.page.models import Page
from feincms.content.raw.models import RawContent
from feincms.content.image.models import ImageContent
from feincms.content.medialibrary.models import MediaFileContent
from feincms.content.application.models import ApplicationContent
from feincms.module.page.extensions.navigation import (
    NavigationExtension, PagePretender)
from feincms.content.application.models import app_reverse


Page.register_templates({
    'key': 'base',
    'title': 'Base Template',
    'path': 'base.html',
    'regions': (
        ('main', 'Main region'),
        ('sidebar', 'Sidebar', 'inherited'),
    ),
})
Page.create_content_type(RawContent)
Page.create_content_type(
    MediaFileContent,
    TYPE_CHOICES=(
        ('default', 'Default position'),
    ),
)
Page.create_content_type(
    ImageContent,
    POSITION_CHOICES=(
        ('default', 'Default position'),
    ),
)


def get_admin_fields(form, *args, **kwargs):
    return {
        'exclusive_subpages': forms.BooleanField(
            label=capfirst(_('exclusive subpages')),
            required=False,
            initial=form.instance.parameters.get('exclusive_subpages', False),
            help_text=_(
                'Exclude everything other than the application\'s'
                ' content when rendering subpages.'),
        ),
    }


Page.create_content_type(ApplicationContent, APPLICATIONS=(
    ('blog_urls', 'Blog', {
        'admin_fields': get_admin_fields,
        'urls': 'example.blog_urls',
    }),
))


Entry.register_regions(
    ('main', 'Main region'),
)
Entry.create_content_type(RawContent)
Entry.create_content_type(
    ImageContent,
    POSITION_CHOICES=(
        ('default', 'Default position'),
    )
)


class BlogEntriesNavigationExtension(NavigationExtension):
    """
    Extended navigation for blog entries.

    It would be added to 'Blog' page properties in admin.
    """
    name = _('all blog entries')

    def children(self, page, **kwargs):
        for entry in Entry.objects.all():
            yield PagePretender(
                title=entry.title,
                url=app_reverse(
                    'blog_entry_detail', 'blog_urls', kwargs={'pk': entry.id}),
                level=page.level + 1,
            )

Page.register_extensions(
    'feincms.module.page.extensions.navigation',
    'feincms.module.page.extensions.sites',
)


@python_2_unicode_compatible
class Category(MPTTModel):
    name = models.CharField(max_length=20)
    slug = models.SlugField()
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children')

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


# add m2m field to entry so it shows up in entry admin
Entry.add_to_class(
    'categories',
    models.ManyToManyField(Category, blank=True, null=True))
EntryAdmin.list_filter += ('categories',)
