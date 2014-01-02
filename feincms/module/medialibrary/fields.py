# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db import models
from django.utils import six
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline
from feincms.utils import shorten_string
from .models import MediaFile
from .thumbnail import admin_thumbnail


__all__ = ('MediaFileForeignKey', 'ContentWithMediaFile')


# ------------------------------------------------------------------------
class MediaFileForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    def __init__(self, original):
        self.__dict__ = original.__dict__

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(
                **{key: value})
            label = ['&nbsp;<strong>%s</strong>' % escape(
                shorten_string(six.text_type(obj)))]
            image = admin_thumbnail(obj)

            if image:
                label.append(
                    '<br /><img src="%s" alt="" style="margin:1em 0 0 10em"'
                    '/>' % image)

            return ''.join(label)
        except (ValueError, self.rel.to.DoesNotExist):
            return ''


class MediaFileForeignKey(models.ForeignKey):
    """
    Drop-in replacement for Django's ``models.ForeignKey`` which automatically
    adds a thumbnail of media files if the media file foreign key is shown
    using ``raw_id_fields``.
    """
    def formfield(self, **kwargs):
        if 'widget' in kwargs and isinstance(
                kwargs['widget'], ForeignKeyRawIdWidget):
            kwargs['widget'] = MediaFileForeignKeyRawIdWidget(kwargs['widget'])
        return super(MediaFileForeignKey, self).formfield(**kwargs)


class ContentWithMediaFile(models.Model):
    class feincms_item_editor_inline(FeinCMSInline):
        raw_id_fields = ('mediafile',)

    mediafile = MediaFileForeignKey(
        MediaFile, verbose_name=_('media file'), related_name='+')

    class Meta:
        abstract = True


# ------------------------------------------------------------------------
class AdminFileWithPreviewWidget(AdminFileWidget):
    """
    Simple AdminFileWidget, but detects if the file is an image and
    tries to render a small thumbnail besides the input field.
    """
    def render(self, name, value, attrs=None):
        r = super(AdminFileWithPreviewWidget, self).render(
            name, value, attrs=attrs)

        if value and getattr(value, 'instance', None):
            image = admin_thumbnail(value.instance)
            if image:
                r = mark_safe((
                    '<img src="%s" alt="" style="float: left; padding-right:'
                    '8px; border-right: 1px solid #ccc; margin-right: 8px"'
                    '>' % image) + r)

        return r

# ------------------------------------------------------------------------

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(
        rules=[((MediaFileForeignKey,), [], {},)],
        patterns=["^feincms\.module\.medialibrary\.fields"])
except ImportError:
    pass
