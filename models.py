from datetime import datetime

from django.db import models
from django.template.defaultfilters import filesizeformat
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from feinheit.translations import TranslatedObjectMixin, Translation,\
    TranslatedObjectManager

import mptt


class Category(models.Model):
    title = models.CharField(_('title'), max_length=200)
    parent = models.ForeignKey('self', blank=True, null=True,
        related_name='children', limit_choices_to={'parent__isnull': True},
        verbose_name=_('parent'))

    class Meta:
        ordering = ['parent__title', 'title']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __unicode__(self):
        if self.parent_id:
            return u'%s - %s' % (self.parent.title, self.title)

        return self.title


class MediaFile(models.Model, TranslatedObjectMixin):
    file = models.ImageField(_('file'), upload_to='medialibrary/%Y/%m/')
    created = models.DateTimeField(_('created'), default=datetime.now)

    categories = models.ManyToManyField(Category, verbose_name=_('categories'))

    class Meta:
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    objects = TranslatedObjectManager()


class MediaFileTranslation(Translation(MediaFile)):
    caption = models.CharField(_('caption'), max_length=200)
    copyright = models.CharField(_('copyright'), max_length=200, blank=True)

    class Meta:
        verbose_name = _('media file translation')
        verbose_name_plural = _('media file translations')

    def __unicode__(self):
        return u'%s (%s / %s)' % (
            self.caption,
            self.parent.file.name[21:], # only show filename
            filesizeformat(self.parent.file.size),
            )


# FeinCMS connector
class MediaFileContent(models.Model):
    mediafile = models.ForeignKey(MediaFile, verbose_name=_('media file'))

    class Meta:
        abstract = True
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    def render(self, **kwargs):
        return self.mediafile.file.name
