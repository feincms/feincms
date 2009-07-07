from datetime import datetime
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.translations import TranslatedObjectMixin, Translation,\
    TranslatedObjectManager


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


class MediaFile(models.Model, TranslatedObjectMixin):
    from django.core.files.storage import FileSystemStorage
    fs = FileSystemStorage(location=settings.FEINCMS_MEDIALIBRARY_PATH,
                           base_url=settings.FEINCMS_MEDIALIBRARY_URL)

    file = models.FileField(_('file'), upload_to=settings.FEINCMS_MEDIALIBRARY_FILES, storage=fs)
    created = models.DateTimeField(_('created'), default=datetime.now)
    copyright = models.CharField(_('copyright'), max_length=200, blank=True)

    categories = models.ManyToManyField(Category, verbose_name=_('categories'))

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

    @property
    def file_name(self):
        return self.file.name

    @property
    def file_url(self):
        return self.file.url

    def get_absolute_url(self):
        return self.file_url

    @property
    def file_type(self):
        import re
        
        FILE_TYPES = (
            ('image', re.compile(r'.(jpg|jpeg|gif|png)$', re.IGNORECASE)),
            ('pdf',   re.compile(r'.pdf$', re.IGNORECASE)),
        )
        
        filename = self.file_name
        for ftype, pat in FILE_TYPES:
            if pat.search(filename):
                return ftype
        return 'other'


class MediaFileTranslation(Translation(MediaFile)):
    caption = models.CharField(_('caption'), max_length=200)

    class Meta:
        verbose_name = _('media file translation')
        verbose_name_plural = _('media file translations')

    def __unicode__(self):
        return u'%s (%s / %s)' % (
            self.caption,
            self.parent.file.name[21:], # only show filename
            filesizeformat(self.parent.file.size),
            )

