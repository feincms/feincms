"""
Simple image inclusion content: You should probably use the media library
instead.
"""

import os

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from feincms import settings

class ImageContent(models.Model):
    # You should probably use
    # `feincms.content.medialibrary.models.MediaFileContent` instead.

    """
    Create an ImageContent like this::

        Cls.create_content_type(
            ImageContent,
            POSITION_CHOICES=(
                ('left', 'Left'),
                ('right', 'Right'),
            ),
            SIZE_CHOICES=(
                ('', 'Do not resize'),
                ('100x100 crop', 'Square Thumbnail'),
                ('200x450 upscale crop', 'Medium Portait'),
                ('1000x1000', 'Large'),
            ))

        Note that SIZE_CHOICES is optional, requires easy_thumbnails to be
        installed.

        Also note that only boolean easy_thumbnail arguments are supported,
        not those with values such as "quality=90".
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
        return render_to_string([
            'content/image/%s.html' % self.position,
            'content/image/default.html',
            ], {'content': self})

    def get_image(self):
        try:
            from easy_thumbnails.files import get_thumbnailer
        except ImportError:
            return self.image
        else:
            size, space, options = getattr(self, 'format', '').partition(' ')
            thumbnailer = get_thumbnailer(self.image)
            thumbnail_options = {'size': size.split('x')}
            for option in options.split(' '):
                thumbnail_options[option] = True
            return thumbnailer.get_thumbnail(thumbnail_options)

    @classmethod
    def initialize_type(cls, POSITION_CHOICES=None, FORMAT_CHOICES=None):
        if POSITION_CHOICES is None:
            raise ImproperlyConfigured(
                'You need to set POSITION_CHOICES when creating a %s' %
                cls.__name__)

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
