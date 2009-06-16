import re

from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms.module.medialibrary.models import MediaFile


class MediaFileWidget(forms.TextInput):
    """
    TextInput widget, shows a link to the current value if there is one.
    """

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

    TYPES = (
        ('image', re.compile(r'.(jpg|jpeg|gif|png)$', re.IGNORECASE)),
        ('pdf', re.compile(r'.pdf$', re.IGNORECASE)),
        ('download', re.compile(r'')),
        )

    mediafile = models.ForeignKey(MediaFile, verbose_name=_('media file'))

    class Meta:
        abstract = True
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    @classmethod
    def handle_kwargs(cls, POSITION_CHOICES=(), TYPES=None):
        models.CharField(_('position'), max_length=10, choices=POSITION_CHOICES
            ).contribute_to_class(cls, 'position')

        if TYPES:
            cls.TYPES = TYPES

    @property
    def type(self):
        filename = self.mediafile.file.name
        for identifier, expression in self.TYPES:
            if expression.search(filename):
                return identifier

        return 'unknown'

    def render(self, **kwargs):
        return render_to_string([
            'content/mediafile/%s_%s.html' % (self.type, self.position),
            'content/mediafile/%s.html' % self.type,
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
