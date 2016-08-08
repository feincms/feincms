from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms._internal import ct_render_to_string
from feincms.contrib.richtext import RichTextField


class RichTextContent(models.Model):
    """
    Rich text content. Uses TinyMCE by default, but can be configured to do
    anything you want using ``FEINCMS_RICHTEXT_INIT_CONTEXT`` and
    ``FEINCMS_RICHTEXT_INIT_TEMPLATE``.

    If you are using TinyMCE 4.x then ``FEINCMS_RICHTEXT_INIT_TEMPLATE``
    needs to be set to ``admin/content/richtext/init_tinymce4.html``.

    Optionally runs the HTML code through HTML cleaners if you specify
    ``cleanse=True`` when calling ``create_content_type``.
    """

    feincms_item_editor_context_processors = (
        lambda x: settings.FEINCMS_RICHTEXT_INIT_CONTEXT,
    )
    feincms_item_editor_includes = {
        'head': [settings.FEINCMS_RICHTEXT_INIT_TEMPLATE],
    }

    class Meta:
        abstract = True
        verbose_name = _('rich text')
        verbose_name_plural = _('rich texts')

    def render(self, **kwargs):
        return ct_render_to_string(
            'content/richtext/default.html',
            {'content': self},
            request=kwargs.get('request'),
            context=kwargs.get('context'),
        )

    @classmethod
    def initialize_type(cls, cleanse=None):
        cls.add_to_class(
            'text',
            RichTextField(_('text'), blank=True, cleanse=cleanse),
        )
