from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminRadioSelect
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms.admin.editor import ItemEditorForm
from feincms.module.medialibrary.models import MediaFile
from feincms.templatetags import feincms_thumbnail


class MediaFileWidget(forms.TextInput):
    """
    TextInput widget, shows a link to the current value if there is one.
    """

    def render(self, name, value, attrs=None):
        inputfield = super(MediaFileWidget, self).render(name, value, attrs)
        if value:
            try:
                mf = MediaFile.objects.get(pk=value)
            except MediaFile.DoesNotExist:
                return inputfield

            try:
                caption = mf.translation.caption
            except ObjectDoesNotExist:
                caption = _('(no caption)')

            if mf.type == 'image':
                image = feincms_thumbnail.thumbnail(mf.file.name, '240x120')
                image = u'<img src="%(url)s" alt="" /><br />' % {'url': image}
            else:
                image = u''

            return mark_safe(u"""
                <div style="margin-left:10em">%(image)s
                <a href="%(url)s" target="_blank">%(caption)s - %(url)s</a><br />
                %(inputfield)s
                </div>""" % {
                    'image': image,
                    'url': mf.file.url,
                    'caption': caption,
                    'inputfield': inputfield})

        return inputfield


# FeinCMS connector
class MediaFileContent(models.Model):
    feincms_item_editor_includes = {
        'head': ['admin/content/mediafile/init.html'],
        }

    class Meta:
        abstract = True
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    @classmethod
    def initialize_type(cls, POSITION_CHOICES=None, MEDIAFILE_CLASS=MediaFile):
        if 'feincms.module.medialibrary' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured, 'You have to add \'feincms.module.medialibrary\' to your INSTALLED_APPS before creating a %s' % cls.__name__

        if POSITION_CHOICES is None:
            raise ImproperlyConfigured, 'You need to set POSITION_CHOICES when creating a %s' % cls.__name__

        cls.add_to_class('mediafile', models.ForeignKey(MEDIAFILE_CLASS, verbose_name=_('media file'),
            related_name='%s_%s_set' % (cls._meta.app_label, cls._meta.module_name)
            ))

        cls.add_to_class('position', models.CharField(_('position'),
            max_length=10, choices=POSITION_CHOICES,
            default=POSITION_CHOICES[0][0]))

        class MediaFileContentAdminForm(ItemEditorForm):
            mediafile = forms.ModelChoiceField(queryset=MEDIAFILE_CLASS.objects.all(),
                widget=MediaFileWidget, label=_('media file'))
            position = forms.ChoiceField(choices=POSITION_CHOICES,
                initial=POSITION_CHOICES[0][0], label=_('position'),
                widget=AdminRadioSelect(attrs={'class': 'radiolist'}))

        cls.feincms_item_editor_form = MediaFileContentAdminForm

    def render(self, **kwargs):
        request = kwargs.get('request')
        return render_to_string([
            'content/mediafile/%s_%s.html' % (self.mediafile.type, self.position),
            'content/mediafile/%s.html' % self.mediafile.type,
            'content/mediafile/%s.html' % self.position,
            'content/mediafile/default.html',
            ], { 'content': self, 'request': request })


    @classmethod
    def default_create_content_type(cls, cms_model):
        return cms_model.create_content_type(cls, POSITION_CHOICES=(
            ('block', _('block')),
            ('left', _('left')),
            ('right', _('right')),
            ))
