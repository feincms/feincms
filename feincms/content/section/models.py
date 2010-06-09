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
    feincms_item_editor_context_processors = (
        lambda x: dict(TINYMCE_JS_URL = settings.TINYMCE_JS_URL),
        lambda x: dict(TINYMCE_CONTENT_CSS_URL = settings.TINYMCE_CONTENT_CSS_URL),
        lambda x: dict(TINYMCE_LINK_LIST_URL = settings.TINYMCE_LINK_LIST_URL),
    )
    feincms_item_editor_includes = {
        'head': [
            settings.TINYMCE_CONFIG_URL,
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
    def initialize_type(cls, TYPE_CHOICES=None, cleanse=False):
        if 'feincms.module.medialibrary' not in django_settings.INSTALLED_APPS:
            raise ImproperlyConfigured, 'You have to add \'feincms.module.medialibrary\' to your INSTALLED_APPS before creating a %s' % cls.__name__

        if TYPE_CHOICES is None:
            raise ImproperlyConfigured, 'You need to set TYPE_CHOICES when creating a %s' % cls.__name__

        cls.add_to_class('mediafile', models.ForeignKey(MediaFile, verbose_name=_('media file'),
            related_name='%s_%s_set' % (cls._meta.app_label, cls._meta.module_name),
            blank=True, null=True,
            ))

        cls.add_to_class('type', models.CharField(_('type'),
            max_length=10, choices=TYPE_CHOICES,
            default=TYPE_CHOICES[0][0]))

        class MediaFileContentAdminForm(ItemEditorForm):
            mediafile = forms.ModelChoiceField(queryset=MediaFile.objects.all(),
                widget=MediaFileWidget, required=False)
            type = forms.ChoiceField(choices=TYPE_CHOICES,
                initial=TYPE_CHOICES[0][0], label=_('type'),
                widget=AdminRadioSelect(attrs={'class': 'radiolist'}))
            feincms_item_editor_classes = {'richtext': 'tinymce',}
            def __init__(self, *args, **kwargs):
                super(MediaFileContentAdminForm, self).__init__(*args, **kwargs)
                for field in self.feincms_item_editor_classes.keys():
                    self.fields[field].widget.attrs.update({'class': 'item-richtext-%s' % self.feincms_item_editor_classes[field]})

        cls.feincms_item_editor_form = MediaFileContentAdminForm
        cls.form = MediaFileContentAdminForm
        cls.cleanse = cleanse

    @classmethod
    def get_queryset(cls, filter_args):
        # Explicitly add nullable FK mediafile to minimize the DB query count
        return cls.objects.select_related('parent', 'mediafile').filter(filter_args)

    def render(self, **kwargs):
        if self.mediafile:
            mediafile_type = self.mediafile.type
        else:
            mediafile_type = 'nomedia'

        return render_to_string([
            'content/section/%s_%s.html' % (self.type, mediafile_type),
            'content/section/%s.html' % self.type,
            'content/section/%s.html' % mediafile_type,
            'content/section/default.html',
            ], {'content': self})

    def save(self, *args, **kwargs):
        if getattr(self, 'cleanse', False):
            from feincms.utils.html.cleanse import cleanse_html
            self.richtext = cleanse_html(self.richtext)
        super(SectionContent, self).save(*args, **kwargs)
