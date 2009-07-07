# ------------------------------------------------------------------------
# coding=utf8
# $Id$
# ------------------------------------------------------------------------

from datetime import datetime
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.translations import TranslatedObjectMixin, Translation,\
    TranslatedObjectManager

import re

# ------------------------------------------------------------------------
class Category(models.Model):
    title = models.CharField(_('title'), max_length=200)
    parent = models.ForeignKey('self', blank=True, null=True,
        related_name='children', limit_choices_to={'parent__isnull': True},
        verbose_name=_('parent'))

    class Meta:
        ordering = ['parent__title', 'title']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __unicode__(self):
        if self.parent_id:
            return u'%s - %s' % (self.parent.title, self.title)

        return self.title

# ------------------------------------------------------------------------
class MediaFile(models.Model, TranslatedObjectMixin):
    from django.core.files.storage import FileSystemStorage
    fs = FileSystemStorage(location=settings.FEINCMS_MEDIALIBRARY_PATH,
                           base_url=settings.FEINCMS_MEDIALIBRARY_URL)

    file = models.FileField(_('file'), upload_to=settings.FEINCMS_MEDIALIBRARY_FILES, storage=fs)
    type = models.CharField(_('file type'), max_length=12, editable=False, default='other')
    created = models.DateTimeField(_('created'), editable=False, default=datetime.now)
    copyright = models.CharField(_('copyright'), max_length=200, blank=True)

    categories = models.ManyToManyField(Category, verbose_name=_('categories'))

    FILE_TYPES = (
        ( 'image', _('Image'),           lambda f: re.compile(r'\.(jpg|jpeg|gif|png)$', re.IGNORECASE).search(f) ),
        ( 'pdf',   _('PDF document'),    lambda f: f.lower().endswith('.pdf') ),
        ( 'txt',   _('Text'),            lambda f: f.lower().endswith('.txt') ),
        ( 'other', _('Binary'),          lambda f: True ), # Must be last
        )

    FILE_TYPES_DICT = dict( [ ( ft[0], ft[1] ) for ft in FILE_TYPES ] )

    class Meta:
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    objects = TranslatedObjectManager()

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

    def get_absolute_url(self):
        return self.file_url

    def file_type(self):
        return self.FILE_TYPES_DICT[self.type]
    file_type.admin_order_field = 'type'
    file_type = property(file_type)

    def determine_file_type(self, name):
        """
        >>> t = MediaFile()
        >>> t.determine_file_type('foobar.jpg')
        'image'
        >>> t.determine_file_type('foobar.PDF')
        'pdf'
        >>> t.determine_file_type('foobar.jpg.pdf')
        'pdf'
        >>> t.determine_file_type('foobar.jgp')
        'other'
        >>> t.determine_file_type('foobar-jpg')
        'other'
        """
        for type_key, type_name, type_test in self.FILE_TYPES:
            if type_test(name):
                return type_key
        return self.FILE_TYPES[-1]

    def save(self, *args, **kwargs):
        if self.id is None:
            created = datetime.now()
        self.type = self.determine_file_type(self.file.name)
            
        super(MediaFile, self).save(*args, **kwargs)

# ------------------------------------------------------------------------
class MediaFileTranslation(Translation(MediaFile)):
    caption = models.CharField(_('caption'), max_length=200)

    class Meta:
        verbose_name = _('media file translation')
        verbose_name_plural = _('media file translations')

    def __unicode__(self):
        from os.path import basename
        
        return u'%s (%s / %s)' % (
            self.caption,
            basename(self.parent.file.name),
            filesizeformat(self.parent.file.size),
            )

#-------------------------------------------------------------------------
#-------------------------------------------------------------------------
