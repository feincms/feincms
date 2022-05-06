# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


from django.contrib.admin.widgets import AdminFileWidget, ForeignKeyRawIdWidget
from django.db import models
from django.utils.html import escape, mark_safe
from django.utils.translation import gettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline
from feincms.utils import shorten_string

from .models import MediaFile
from .thumbnail import admin_thumbnail


__all__ = ("MediaFileForeignKey", "ContentWithMediaFile")


# ------------------------------------------------------------------------
class MediaFileForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    def __init__(self, original):
        self.__dict__ = original.__dict__

    def label_and_url_for_value(self, value):
        label, url = super().label_and_url_for_value(value)
        key = "pk"
        try:
            obj = (
                self.rel.model._default_manager.using(self.db)
                .filter(**{key: value})
                .first()
            )
            label = ["&nbsp;<strong>%s</strong>" % escape(shorten_string(str(obj)))]
            image = admin_thumbnail(obj)

            if image:
                label.append(
                    '<br /><img src="%s" alt="" style="margin:1em 0 0 170px"'
                    "/>" % image
                )

            return mark_safe("".join(label)), url
        except (ValueError, self.rel.model.DoesNotExist):
            return label, url


class MediaFileForeignKey(models.ForeignKey):
    """
    Drop-in replacement for Django's ``models.ForeignKey`` which automatically
    adds a thumbnail of media files if the media file foreign key is shown
    using ``raw_id_fields``.
    """

    def __init__(self, *args, **kwargs):
        if not args and "to" not in kwargs:
            args = (MediaFile,)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        if "widget" in kwargs and isinstance(kwargs["widget"], ForeignKeyRawIdWidget):
            kwargs["widget"] = MediaFileForeignKeyRawIdWidget(kwargs["widget"])
        return super().formfield(**kwargs)


class ContentWithMediaFile(models.Model):
    class feincms_item_editor_inline(FeinCMSInline):
        raw_id_fields = ("mediafile",)

    mediafile = MediaFileForeignKey(
        MediaFile,
        verbose_name=_("media file"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    class Meta:
        abstract = True


# ------------------------------------------------------------------------
class AdminFileWithPreviewWidget(AdminFileWidget):
    """
    Simple AdminFileWidget, but detects if the file is an image and
    tries to render a small thumbnail besides the input field.
    """

    def render(self, name, value, attrs=None, *args, **kwargs):
        r = super().render(name, value, attrs=attrs, *args, **kwargs)

        if value and getattr(value, "instance", None):
            image = admin_thumbnail(value.instance)
            if image:
                r = mark_safe(
                    (
                        '<img src="%s" alt="" style="float: left; padding-right:'
                        '8px; border-right: 1px solid #ccc; margin-right: 8px"'
                        ">" % image
                    )
                    + r
                )

        return r
