from __future__ import unicode_literals

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline
from feincms.module.medialibrary.fields import ContentWithMediaFile


class MediaFileContentInline(FeinCMSInline):
    raw_id_fields = ('mediafile',)
    radio_fields = {'type': admin.VERTICAL}


class MediaFileContent(ContentWithMediaFile):
    """
    Rehashed, backwards-incompatible media file content which does not contain
    the problems from v1 anymore.

    Create a media file content as follows::

        from feincms.content.medialibrary.v2 import MediaFileContent
        Page.create_content_type(MediaFileContent, TYPE_CHOICES=(
            ('default', _('Default')),
            ('lightbox', _('Lightbox')),
            ('whatever', _('Whatever')),
            ))

    For a media file of type 'image' and type 'lightbox', the following
    templates are tried in order:

    * content/mediafile/image_lightbox.html
    * content/mediafile/image.html
    * content/mediafile/lightbox.html
    * content/mediafile/default.html

    The context contains ``content`` and ``request`` (if available).
    """

    feincms_item_editor_inline = MediaFileContentInline

    class Meta:
        abstract = True
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    @classmethod
    def initialize_type(cls, TYPE_CHOICES=None):
        if TYPE_CHOICES is None:
            raise ImproperlyConfigured(
                'You have to set TYPE_CHOICES when'
                ' creating a %s' % cls.__name__)

        cls.add_to_class(
            'type',
            models.CharField(
                _('type'),
                max_length=20,
                choices=TYPE_CHOICES,
                default=TYPE_CHOICES[0][0],
            )
        )

    def render(self, **kwargs):
        ctx = {'content': self}
        ctx.update(kwargs)
        return render_to_string([
            'content/mediafile/%s_%s.html' % (self.mediafile.type, self.type),
            'content/mediafile/%s.html' % self.mediafile.type,
            'content/mediafile/%s.html' % self.type,
            'content/mediafile/default.html',
        ], ctx, context_instance=kwargs.get('context'))
