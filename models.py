from datetime import datetime
import re

from django import forms
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
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
    TYPES = (
        ('image', re.compile(r'.(jpg|jpeg|gif|png)$', re.IGNORECASE)),
        ('pdf', re.compile(r'.pdf$', re.IGNORECASE)),
        ('download', re.compile(r'')),
        )

    file = models.FileField(_('file'), upload_to='medialibrary/%Y/%m/')
    created = models.DateTimeField(_('created'), default=datetime.now)
    copyright = models.CharField(_('copyright'), max_length=200, blank=True)

    categories = models.ManyToManyField(Category, verbose_name=_('categories'))

    class Meta:
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    objects = TranslatedObjectManager()

    @property
    def type(self):
        filename = self.file.name
        for identifier, expression in self.TYPES:
            if expression.search(filename):
                return identifier


class MediaFileTranslation(Translation(MediaFile)):
    caption = models.CharField(_('caption'), max_length=200)

    class Meta:
        verbose_name = _('media file translation')
        verbose_name_plural = _('media file translations')

    def __unicode__(self):
        return u'%s (%s / %s)' % (
            self.caption,
            self.parent.file.name[21:], # only show filename
            filesizeformat(self.parent.file.size),
            )


class MediaFileWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        inputfield = super(MediaFileWidget, self).render(name, value, attrs)
        if value:
            try:
                mf = MediaFile.objects.get(pk=value)
                return mark_safe(u"""
                    <a href="%(url)s" target="_blank">%(caption)s (%(url)s)</a><br />
                    %(inputfield)s""" % {
                        'url': mf.file.url,
                        'caption': mf.translation.caption,
                        'inputfield': inputfield})
            except:
                pass

        return inputfield


class MediaFileContentAdminForm(forms.ModelForm):
    mediafile = forms.ModelChoiceField(queryset=MediaFile.objects.all(),
        widget=MediaFileWidget)


# FeinCMS connector
class MediaFileContent(models.Model):
    feincms_item_editor_form = MediaFileContentAdminForm
    feincms_item_editor_includes = {
        'head': ['admin/content/mediafile/init.html'],
        }


    mediafile = models.ForeignKey(MediaFile, verbose_name=_('media file'))

    class Meta:
        abstract = True
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    @classmethod
    def handle_kwargs(cls, POSITION_CHOICES=()):
        models.CharField(_('position'), max_length=10, choices=POSITION_CHOICES
            ).contribute_to_class(cls, 'position')

    def render(self, **kwargs):
        return render_to_string([
            'content/mediafile/%s_%s.html' % (self.mediafile.type, self.position),
            'content/mediafile/%s.html' % self.mediafile.type,
            'content/mediafile/%s.html' % self.position,
            'content/mediafile/default.html',
            ], {'content': self})


    @classmethod
    def default_create_content_type(cls, cms_model):
        return cms_model.create_content_type(cls, POSITION_CHOICES=(
            ('block', _('block')),
            ('left', _('left')),
            ('right', _('right')),
            ))
