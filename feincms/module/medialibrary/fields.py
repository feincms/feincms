from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.db import models
from django.utils.html import escape
from django.utils.text import truncate_words
from django.utils.translation import ugettext_lazy as _

from feincms.admin.item_editor import FeinCMSInline
from feincms.module.medialibrary.models import MediaFile
from feincms.templatetags import feincms_thumbnail


__all__ = ('MediaFileForeignKey', 'ContentWithMediaFile')


class MediaFileForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    def __init__(self, original):
        self.__dict__ = original.__dict__

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            label = [u'&nbsp;<strong>%s</strong>' % escape(truncate_words(obj, 14))]

            if obj.type == 'image':
                image = feincms_thumbnail.thumbnail(obj.file.name, '240x120')
                label.append(u'<br /><img src="%s" alt="" style="margin:1em 0 0 10em" />' % image)

            return u''.join(label)
        except (ValueError, self.rel.to.DoesNotExist):
            return ''


class MediaFileForeignKey(models.ForeignKey):
    def formfield(self, **kwargs):
        if 'widget' in kwargs and isinstance(kwargs['widget'], ForeignKeyRawIdWidget):
            kwargs['widget'] = MediaFileForeignKeyRawIdWidget(kwargs['widget'])
        return super(MediaFileForeignKey, self).formfield(**kwargs)


class ContentWithMediaFile(models.Model):
    class feincms_item_editor_inline(FeinCMSInline):
        raw_id_fields = ('mediafile',)

    mediafile = MediaFileForeignKey(MediaFile, verbose_name=_('media file'),
        related_name='+')

    class Meta:
        abstract = True


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[((MediaFileForeignKey,), [], {},)],
        patterns=["^feincms\.module\.medialibrary\.fields"])
except ImportError:
    pass
