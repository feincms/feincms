from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


def tinymce_js_url(request):
    return {
        'TINYMCE_JS_URL': getattr(settings, 'TINYMCE_JS_URL',
            settings.MEDIA_URL + 'js/tiny_mce/tiny_mce.js'),
            }

class RichTextContent(models.Model):
    feincms_item_editor_context_processors = (tinymce_js_url,)
    feincms_item_editor_includes = {
        'head': ['admin/content/richtext/init.html'],
        }

    text = models.TextField(_('text'), blank=True)

    class Meta:
        abstract = True
        verbose_name = _('rich text')
        verbose_name_plural = _('rich texts')

    def render(self, **kwargs):
        return mark_safe(self.text)

