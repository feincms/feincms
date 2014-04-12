# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import os
import re

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.models import ExtensionsMixin
from feincms.translations import (
    TranslatedObjectMixin, Translation, TranslatedObjectManager)

from . import logger


# ------------------------------------------------------------------------
class CategoryManager(models.Manager):
    """
    Simple manager which exists only to supply ``.select_related("parent")``
    on querysets since we can't even __str__ efficiently without it.
    """
    def get_query_set(self):
        return super(CategoryManager, self).get_query_set().select_related(
            "parent")


# ------------------------------------------------------------------------
@python_2_unicode_compatible
class Category(models.Model):
    """
    These categories are meant primarily for organizing media files in the
    library.
    """

    title = models.CharField(_('title'), max_length=200)
    parent = models.ForeignKey(
        'self', blank=True, null=True,
        related_name='children', limit_choices_to={'parent__isnull': True},
        verbose_name=_('parent'))

    slug = models.SlugField(_('slug'), max_length=150)

    class Meta:
        ordering = ['parent__title', 'title']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    objects = CategoryManager()

    def __str__(self):
        if self.parent_id:
            return '%s - %s' % (self.parent.title, self.title)

        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Category, self).save(*args, **kwargs)
    save.alters_data = True

    def path_list(self):
        if self.parent is None:
            return [self]
        p = self.parent.path_list()
        p.append(self)
        return p

    def path(self):
        return ' - '.join((f.title for f in self.path_list()))


# ------------------------------------------------------------------------
@python_2_unicode_compatible
class MediaFileBase(models.Model, ExtensionsMixin, TranslatedObjectMixin):
    """
    Abstract media file class. Includes the
    :class:`feincms.models.ExtensionsMixin` because of the (handy) extension
    mechanism.
    """

    file = models.FileField(
        _('file'), max_length=255,
        upload_to=settings.FEINCMS_MEDIALIBRARY_UPLOAD_TO)
    type = models.CharField(
        _('file type'), max_length=12, editable=False,
        choices=())
    created = models.DateTimeField(
        _('created'), editable=False, default=timezone.now)
    copyright = models.CharField(_('copyright'), max_length=200, blank=True)
    file_size = models.IntegerField(
        _("file size"), blank=True, null=True, editable=False)

    categories = models.ManyToManyField(
        Category, verbose_name=_('categories'), blank=True, null=True)
    categories.category_filter = True

    class Meta:
        abstract = True
        ordering = ['-created']
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    objects = TranslatedObjectManager()

    filetypes = []
    filetypes_dict = {}

    @classmethod
    def reconfigure(cls, upload_to=None, storage=None):
        f = cls._meta.get_field('file')
        # Ugh. Copied relevant parts from django/db/models/fields/files.py
        # FileField.__init__ (around line 225)
        if storage:
            f.storage = storage
        if upload_to:
            f.upload_to = upload_to
            if callable(upload_to):
                f.generate_filename = upload_to

    @classmethod
    def register_filetypes(cls, *types):
        cls.filetypes[0:0] = types
        choices = [t[0:2] for t in cls.filetypes]
        cls.filetypes_dict = dict(choices)
        cls._meta.get_field('type').choices[:] = choices

    def __init__(self, *args, **kwargs):
        super(MediaFileBase, self).__init__(*args, **kwargs)
        if self.file:
            self._original_file_name = self.file.name

    def __str__(self):
        trans = None

        try:
            trans = self.translation
        except models.ObjectDoesNotExist:
            pass
        except AttributeError:
            pass

        if trans:
            trans = '%s' % trans
            if trans.strip():
                return trans
        return os.path.basename(self.file.name)

    def get_absolute_url(self):
        return self.file.url

    def determine_file_type(self, name):
        """
        >>> t = MediaFileBase()
        >>> str(t.determine_file_type('foobar.jpg'))
        'image'
        >>> str(t.determine_file_type('foobar.PDF'))
        'pdf'
        >>> str(t.determine_file_type('foobar.jpg.pdf'))
        'pdf'
        >>> str(t.determine_file_type('foobar.jgp'))
        'other'
        >>> str(t.determine_file_type('foobar-jpg'))
        'other'
        """
        for type_key, type_name, type_test in self.filetypes:
            if type_test(name):
                return type_key
        return self.filetypes[-1][0]

    def save(self, *args, **kwargs):
        if not self.id and not self.created:
            self.created = timezone.now()

        self.type = self.determine_file_type(self.file.name)
        if self.file:
            try:
                self.file_size = self.file.size
            except (OSError, IOError, ValueError) as e:
                logger.error("Unable to read file size for %s: %s" % (self, e))

        super(MediaFileBase, self).save(*args, **kwargs)

        logger.info("Saved mediafile %d (%s, type %s, %d bytes)" % (
            self.id, self.file.name, self.type, self.file_size or 0))

        # User uploaded a new file. Try to get rid of the old file in
        # storage, to avoid having orphaned files hanging around.
        if getattr(self, '_original_file_name', None):
            if self.file.name != self._original_file_name:
                self.delete_mediafile(self._original_file_name)

        self.purge_translation_cache()
    save.alters_data = True

    def delete_mediafile(self, name=None):
        if name is None:
            name = self.file.name
        try:
            self.file.storage.delete(name)
        except Exception as e:
            logger.warn("Cannot delete media file %s: %s" % (name, e))


# ------------------------------------------------------------------------
MediaFileBase.register_filetypes(
    # Should we be using imghdr.what instead of extension guessing?
    ('image', _('Image'), lambda f: re.compile(
        r'\.(bmp|jpe?g|jp2|jxr|gif|png|tiff?)$', re.IGNORECASE).search(f)),
    ('video', _('Video'), lambda f: re.compile(
        r'\.(mov|m[14]v|mp4|avi|mpe?g|qt|ogv|wmv|flv)$',
        re.IGNORECASE).search(f)),
    ('audio', _('Audio'), lambda f: re.compile(
        r'\.(au|mp3|m4a|wma|oga|ram|wav)$', re.IGNORECASE).search(f)),
    ('pdf', _('PDF document'), lambda f: f.lower().endswith('.pdf')),
    ('swf', _('Flash'), lambda f: f.lower().endswith('.swf')),
    ('txt', _('Text'), lambda f: f.lower().endswith('.txt')),
    ('rtf', _('Rich Text'), lambda f: f.lower().endswith('.rtf')),
    ('zip', _('Zip archive'), lambda f: f.lower().endswith('.zip')),
    ('doc', _('Microsoft Word'), lambda f: re.compile(
        r'\.docx?$', re.IGNORECASE).search(f)),
    ('xls', _('Microsoft Excel'), lambda f: re.compile(
        r'\.xlsx?$', re.IGNORECASE).search(f)),
    ('ppt', _('Microsoft PowerPoint'), lambda f: re.compile(
        r'\.pptx?$', re.IGNORECASE).search(f)),
    ('other', _('Binary'), lambda f: True),  # Must be last
)


# ------------------------------------------------------------------------
class MediaFile(MediaFileBase):
    pass


@receiver(post_delete, sender=MediaFile)
def _mediafile_post_delete(sender, instance, **kwargs):
    instance.delete_mediafile()
    logger.info("Deleted mediafile %d (%s)" % (
        instance.id, instance.file.name))


# ------------------------------------------------------------------------
@python_2_unicode_compatible
class MediaFileTranslation(Translation(MediaFile)):
    """
    Translated media file caption and description.
    """

    caption = models.CharField(_('caption'), max_length=200)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        verbose_name = _('media file translation')
        verbose_name_plural = _('media file translations')
        unique_together = ('parent', 'language_code')

    def __str__(self):
        return self.caption
