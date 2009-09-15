from django import forms
from django.conf import settings as django_settings
from django.contrib.admin.widgets import AdminRadioSelect
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.admin.editor import ItemEditorForm
from feincms.module.medialibrary.models import MediaFile

from feincms.content.medialibrary.models import MediaFileWidget

class SectionContent(models.Model):
    feincms_item_editor_context_processors = ( lambda x: dict(TINYMCE_JS_URL = settings.TINYMCE_JS_URL), )
    feincms_item_editor_includes = {
        'head': [
            'admin/content/richtext/init.html',
            'admin/content/mediafile/init.html',
            ],
        }

    title = models.CharField(_('title'), max_length=200, blank=True)
    richtext = models.TextField(_('text'), blank=True)

    class Meta:
        abstract = True
        verbose_name = _('section')
        verbose_name_plural = _('sections')

    @classmethod
    def initialize_type(cls, POSITION_CHOICES=None, cleanse=False):
        if 'feincms.module.medialibrary' not in django_settings.INSTALLED_APPS:
            raise ImproperlyConfigured, 'You have to add \'feincms.module.medialibrary\' to your INSTALLED_APPS before creating a %s' % cls.__name__

        if POSITION_CHOICES is None:
            raise ImproperlyConfigured, 'You need to set POSITION_CHOICES when creating a %s' % cls.__name__

        cls.add_to_class('mediafile', models.ForeignKey(MediaFile, verbose_name=_('media file'),
            related_name='%s_%s_set' % (cls._meta.app_label, cls._meta.module_name),
            blank=True, null=True,
            ))

        cls.add_to_class('position', models.CharField(_('position'),
            max_length=10, choices=POSITION_CHOICES,
            default=POSITION_CHOICES[0][0]))

        class MediaFileContentAdminForm(ItemEditorForm):
            mediafile = forms.ModelChoiceField(queryset=MediaFile.objects.all(),
                widget=MediaFileWidget, required=False)
            position = forms.ChoiceField(choices=POSITION_CHOICES,
                initial=POSITION_CHOICES[0][0], label=_('position'),
                widget=AdminRadioSelect(attrs={'class': 'radiolist'}))

        cls.feincms_item_editor_form = MediaFileContentAdminForm
        cls.cleanse = cleanse

    def render(self, **kwargs):
        return render_to_string([
            'content/section/%s_%s.html' % (self.mediafile.type, self.position),
            'content/section/%s.html' % self.mediafile.type,
            'content/section/%s.html' % self.position,
            'content/section/default.html',
            ], {'content': self})

    def save(self, *args, **kwargs):
        if getattr(self, 'cleanse', False):
            from feincms.content.richtext.cleanse import cleanse_html
            self.richtext = cleanse_html(self.richtext)
        super(SectionContent, self).save(*args, **kwargs)
