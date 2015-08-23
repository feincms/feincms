from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.admin.item_editor import FeinCMSInline
from feincms.contrib.richtext import RichTextField
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


class RawContent(models.Model):
    """
    Content type which can be used to input raw HTML code into the CMS.

    The content isn't escaped and can be used to insert CSS or JS
    snippets too.
    """

    text = models.TextField(_('content'), blank=True)

    class Meta:
        abstract = True
        verbose_name = _('raw content')
        verbose_name_plural = _('raw contents')

    def render(self, **kwargs):
        return mark_safe(self.text)


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

    text = RichTextField(_('text'), blank=True)

    class Meta:
        abstract = True
        verbose_name = _('rich text')
        verbose_name_plural = _('rich texts')

    def render(self, **kwargs):
        return render_to_string(
            'content/richtext/default.html',
            {'content': self},
            context_instance=kwargs.get('context'))

    def save(self, *args, **kwargs):
        if getattr(self, 'cleanse', None):
            # Passes the rich text content as first argument because
            # the passed callable has been converted into a bound method
            self.text = self.cleanse(self.text)

        super(RichTextContent, self).save(*args, **kwargs)
    save.alters_data = True

    @classmethod
    def initialize_type(cls, cleanse=None):
        def to_instance_method(func):
            def func_im(self, *args, **kwargs):
                return func(*args, **kwargs)
            return func_im

        if cleanse:
            cls.cleanse = to_instance_method(cleanse)


try:
    from filer.fields.file import FilerFileField
    from filer.fields.image import FilerImageField
except ImportError:
    pass
else:

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
            ctx = {'content': self}
            ctx.update(kwargs)
            return render_to_string([
                'content/filer/%s_%s.html' % (self.file_type, self.type),
                'content/filer/%s.html' % self.type,
                'content/filer/%s.html' % self.file_type,
                'content/filer/default.html',
            ], ctx, context_instance=kwargs.get('context'))

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
