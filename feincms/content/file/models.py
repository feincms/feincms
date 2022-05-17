"""
Simple file inclusion content: You should probably use the media library
instead.
"""


import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from feincms import settings
from feincms.utils.tuple import AutoRenderTuple


class FileContent(models.Model):
    # You should probably use
    # `feincms.content.medialibrary.models.MediaFileContent` instead.

    title = models.CharField(max_length=200)
    file = models.FileField(
        _("file"),
        max_length=255,
        upload_to=os.path.join(settings.FEINCMS_UPLOAD_PREFIX, "filecontent"),
    )

    class Meta:
        abstract = True
        verbose_name = _("file")
        verbose_name_plural = _("files")

    def render(self, **kwargs):
        return AutoRenderTuple(
            (
                ["content/file/%s.html" % self.region, "content/file/default.html"],
                {"content": self},
            )
        )
