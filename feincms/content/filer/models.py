from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline
from feincms._internal import ct_render_to_string

try:
    from filer.fields.file import FilerFileField
    from filer.fields.image import FilerImageField
except ImportError:
    __all__ = ()

else:

    __all__ = (
        'MediaFileContentInline', 'ContentWithFilerFile',
        'FilerFileContent', 'FilerImageContent',
    )

    class MediaFileContentInline(FeinCMSInline):
        radio_fields = {'type': admin.VERTICAL}

    class ContentWithFilerFile(models.Model):
        """
        File content
        """
        feincms_item_editor_inline = MediaFileContentInline

        class Meta:
            abstract = True

        def render(self, **kwargs):
            return ct_render_to_string(
                [
                    'content/filer/%s_%s.html' % (self.file_type, self.type),
                    'content/filer/%s.html' % self.type,
                    'content/filer/%s.html' % self.file_type,
                    'content/filer/default.html',
                ],
                {'content': self},
                request=kwargs.get('request'),
                context=kwargs.get('context'),
            )

    class FilerFileContent(ContentWithFilerFile):
        mediafile = FilerFileField(verbose_name=_('file'), related_name='+')
        file_type = 'file'
        type = 'download'

        class Meta:
            abstract = True
            verbose_name = _('file')
            verbose_name_plural = _('files')

    class FilerImageContent(ContentWithFilerFile):
        """
        Create a media file content as follows::

            from feincms.contents import FilerImageContent
            Page.create_content_type(FilerImageContent, TYPE_CHOICES=(
                ('inline', _('Default')),
                ('lightbox', _('Lightbox')),
                ('whatever', _('Whatever')),
            ))

        For a media file of type 'image' and type 'lightbox', the following
        templates are tried in order:

        * content/mediafile/image_lightbox.html
        * content/mediafile/lightbox.html
        * content/mediafile/image.html
        * content/mediafile/default.html

        The context contains ``content`` and ``request`` (if available).

        The content.mediafile attribute are as follows (selection):
        label, description, default_caption, default_alt_text,
        author, must_always_publish_author_credit,
        must_always_publish_copyright, date_taken, file, id, is_public, url
        """

        mediafile = FilerImageField(verbose_name=_('image'), related_name='+')
        caption = models.CharField(
            _('caption'),
            max_length=1000,
            blank=True,
        )
        url = models.CharField(
            _('URL'),
            max_length=1000,
            blank=True,
        )

        file_type = 'image'

        class Meta:
            abstract = True
            verbose_name = _('image')
            verbose_name_plural = _('images')

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
                ),
            )
