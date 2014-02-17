from __future__ import absolute_import, unicode_literals

from django.conf import settings as django_settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.admin.item_editor import FeinCMSInline
from feincms.contrib.richtext import RichTextField
from feincms.module.medialibrary.fields import MediaFileForeignKey
from feincms.module.medialibrary.models import MediaFile


class SectionContentInline(FeinCMSInline):
    raw_id_fields = ('mediafile',)
    radio_fields = {'type': admin.VERTICAL}


class SectionContent(models.Model):
    """
    Title, media file and rich text fields in one content block.
    """

    feincms_item_editor_inline = SectionContentInline
    feincms_item_editor_context_processors = (
        lambda x: settings.FEINCMS_RICHTEXT_INIT_CONTEXT,
    )
    feincms_item_editor_includes = {
        'head': [settings.FEINCMS_RICHTEXT_INIT_TEMPLATE],
    }

    title = models.CharField(_('title'), max_length=200, blank=True)
    richtext = RichTextField(_('text'), blank=True)
    mediafile = MediaFileForeignKey(
        MediaFile, verbose_name=_('media file'),
        related_name='+', blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _('section')
        verbose_name_plural = _('sections')

    @classmethod
    def initialize_type(cls, TYPE_CHOICES=None, cleanse=None):
        if 'feincms.module.medialibrary' not in django_settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                'You have to add \'feincms.module.medialibrary\' to your'
                ' INSTALLED_APPS before creating a %s' % cls.__name__)

        if TYPE_CHOICES is None:
            raise ImproperlyConfigured(
                'You need to set TYPE_CHOICES when creating a'
                ' %s' % cls.__name__)

        cls.add_to_class('type', models.CharField(
            _('type'),
            max_length=10, choices=TYPE_CHOICES,
            default=TYPE_CHOICES[0][0]
        ))

        if cleanse:
            cls.cleanse = cleanse

    @classmethod
    def get_queryset(cls, filter_args):
        # Explicitly add nullable FK mediafile to minimize the DB query count
        return cls.objects.select_related('parent', 'mediafile').filter(
            filter_args)

    def render(self, **kwargs):
        if self.mediafile:
            mediafile_type = self.mediafile.type
        else:
            mediafile_type = 'nomedia'

        return render_to_string(
            [
                'content/section/%s_%s.html' % (mediafile_type, self.type),
                'content/section/%s.html' % mediafile_type,
                'content/section/%s.html' % self.type,
                'content/section/default.html',
            ],
            {'content': self},
        )

    def save(self, *args, **kwargs):
        if getattr(self, 'cleanse', None):
            try:
                # Passes the rich text content as first argument because
                # the passed callable has been converted into a bound method
                self.richtext = self.cleanse(self.richtext)
            except TypeError:
                # Call the original callable, does not pass the rich richtext
                # content instance along
                self.richtext = self.cleanse.im_func(self.richtext)

        super(SectionContent, self).save(*args, **kwargs)
    save.alters_data = True
