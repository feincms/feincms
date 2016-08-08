"""
Simple image inclusion content: You should probably use the media library
instead.
"""

from __future__ import absolute_import, unicode_literals

import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms._internal import ct_render_to_string
from feincms.templatetags import feincms_thumbnail


class ImageContent(models.Model):
    # You should probably use
    # `feincms.content.medialibrary.models.MediaFileContent` instead.

    """
    Create an ImageContent like this::

        Cls.create_content_type(
            ImageContent,
            POSITION_CHOICES=(
                ('left', 'Float to left'),
                ('right', 'Float to right'),
                ('block', 'Block'),
            ),
            FORMAT_CHOICES=(
                ('noop', 'Do not resize'),
                ('cropscale:100x100', 'Square Thumbnail'),
                ('cropscale:200x450', 'Medium Portait'),
                ('thumbnail:1000x1000', 'Large'),
            ))

        Note that FORMAT_CHOICES is optional. The part before the colon
        corresponds to the template filters in the ``feincms_thumbnail``
        template filter library. Known values are ``cropscale`` and
        ``thumbnail``. Everything else (such as ``noop``) is ignored.
    """

    image = models.ImageField(
        _('image'), max_length=255,
        upload_to=os.path.join(settings.FEINCMS_UPLOAD_PREFIX, 'imagecontent'))
    alt_text = models.CharField(
        _('alternate text'), max_length=255, blank=True,
        help_text=_('Description of image'))
    caption = models.CharField(_('caption'), max_length=255, blank=True)

    class Meta:
        abstract = True
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def render(self, **kwargs):
        templates = ['content/image/default.html']
        if hasattr(self, 'position'):
            templates.insert(0, 'content/image/%s.html' % self.position)

        return ct_render_to_string(
            templates,
            {'content': self},
            request=kwargs.get('request'),
            context=kwargs.get('context'),
        )

    def get_image(self):
        type, separator, size = getattr(self, 'format', '').partition(':')
        if not size:
            return self.image

        thumbnailer = {
            'cropscale': feincms_thumbnail.CropscaleThumbnailer,
        }.get(type, feincms_thumbnail.Thumbnailer)
        return thumbnailer(self.image, size)

    @classmethod
    def initialize_type(cls, POSITION_CHOICES=None, FORMAT_CHOICES=None):
        if POSITION_CHOICES:
            models.CharField(
                _('position'),
                max_length=10,
                choices=POSITION_CHOICES,
                default=POSITION_CHOICES[0][0]
            ).contribute_to_class(cls, 'position')

        if FORMAT_CHOICES:
            models.CharField(
                _('format'),
                max_length=64,
                choices=FORMAT_CHOICES,
                default=FORMAT_CHOICES[0][0]
            ).contribute_to_class(cls, 'format')
