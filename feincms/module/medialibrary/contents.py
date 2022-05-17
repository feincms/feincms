from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline
from feincms.module.medialibrary.fields import ContentWithMediaFile
from feincms.utils.tuple import AutoRenderTuple


class MediaFileContentInline(FeinCMSInline):
    raw_id_fields = ("mediafile",)
    radio_fields = {"type": admin.VERTICAL}


class MediaFileContent(ContentWithMediaFile):
    """
    Rehashed, backwards-incompatible media file content which does not contain
    the problems from v1 anymore.

    Create a media file content as follows::

        from feincms.content.medialibrary.models import MediaFileContent
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
        verbose_name = _("media file")
        verbose_name_plural = _("media files")

    @classmethod
    def initialize_type(cls, TYPE_CHOICES=None):
        if TYPE_CHOICES is None:
            raise ImproperlyConfigured(
                "You have to set TYPE_CHOICES when" " creating a %s" % cls.__name__
            )

        cls.add_to_class(
            "type",
            models.CharField(
                _("type"),
                max_length=20,
                choices=TYPE_CHOICES,
                default=TYPE_CHOICES[0][0],
            ),
        )

    def render(self, **kwargs):
        return AutoRenderTuple(
            (
                [
                    f"content/mediafile/{self.mediafile.type}_{self.type}.html",
                    "content/mediafile/%s.html" % self.mediafile.type,
                    "content/mediafile/%s.html" % self.type,
                    "content/mediafile/default.html",
                ],
                {"content": self},
            )
        )
