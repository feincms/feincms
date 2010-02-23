# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from datetime import datetime

from django.contrib import admin
from django.conf import settings as django_settings
from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from feincms import settings
from feincms.models import Base

from feincms.translations import TranslatedObjectMixin, Translation, \
    TranslatedObjectManager

import re
import os
import logging

class CategoryManager(models.Manager):
    """
    Simple manager which exists only to supply ``.select_related("parent")``
    on querysets since we can't even __unicode__ efficiently without it.
    """
    def get_query_set(self):
        return super(CategoryManager, self).get_query_set().select_related("parent")

# ------------------------------------------------------------------------
class Category(models.Model):
    objects = CategoryManager()

    title = models.CharField(_('title'), max_length=200)
    parent = models.ForeignKey('self', blank=True, null=True,
        related_name='children', limit_choices_to={'parent__isnull': True},
        verbose_name=_('parent'))

    slug = models.SlugField(_('slug'), max_length=150)

    class Meta:
        ordering = ['parent__title', 'title']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __unicode__(self):
        if self.parent_id:
            return u'%s - %s' % (self.parent.title, self.title)

        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Category, self).save(*args, **kwargs)


class CategoryAdmin(admin.ModelAdmin):
    list_display      = ['parent', 'title']
    list_filter       = ['parent']
    list_per_page     = 25
    search_fields     = ['title']
    prepopulated_fields = { 'slug': ('title',), }


# ------------------------------------------------------------------------
class MediaFileBase(Base, TranslatedObjectMixin):

    # XXX maybe have a look at settings.DEFAULT_FILE_STORAGE here?
    from django.core.files.storage import FileSystemStorage
    fs = FileSystemStorage(location=settings.FEINCMS_MEDIALIBRARY_ROOT,
                           base_url=settings.FEINCMS_MEDIALIBRARY_URL)

    file = models.FileField(_('file'), max_length=255, upload_to=settings.FEINCMS_MEDIALIBRARY_UPLOAD_TO, storage=fs)
    type = models.CharField(_('file type'), max_length=12, editable=False, choices=())
    created = models.DateTimeField(_('created'), editable=False, default=datetime.now)
    copyright = models.CharField(_('copyright'), max_length=200, blank=True)
    file_size  = models.IntegerField(_("file size"), blank=True, null=True, editable=False)

    categories = models.ManyToManyField(Category, verbose_name=_('categories'),
                                        blank=True, null=True)
    categories.category_filter = True

    class Meta:
        abstract = True
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    objects = TranslatedObjectManager()

    filetypes = [ ]
    filetypes_dict = { }

    def get_categories_as_string(self):
        categories_tmp = self.categories.values_list('title', flat=True)
        return ', '.join(categories_tmp)
    get_categories_as_string.short_description = _('categories')

    def formatted_file_size(self):
        return filesizeformat(self.file_size)
    formatted_file_size.short_description = _("file size")

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
        choices = [ t[0:2] for t in cls.filetypes ]
        cls.filetypes_dict = dict(choices)
        cls._meta.get_field('type').choices[:] = choices

    def __unicode__(self):
        trans = None

        # This might be provided using a .extra() clause to avoid hundreds of extra queries:
        if hasattr(self, "preferred_translation"):
            trans = getattr(self, "preferred_translation", u"")
        else:
            try:
                trans = unicode(self.translation)
            except models.ObjectDoesNotExist:
                pass
            except AttributeError, e:
                pass

        if trans:
            return trans
        else:
            return os.path.basename(self.file.name)

    def get_absolute_url(self):
        return self.file.url

    def file_type(self):
        return self.filetypes_dict[self.type]
    file_type.admin_order_field = 'type'
    file_type.short_description = _('file type')

    def file_info(self):
        """
        Method for showing the file name in admin.

        Note: This also includes a hidden field that can be used to extract
        the file name later on, this can be used to access the file name from
        JS, like for example a TinyMCE connector shim.
        """
        from os.path import basename
        return u'<input type="hidden" class="medialibrary_file_path" name="_media_path_%d" value="%s" /> %s' % (
                self.id,
                self.file.name,
                basename(self.file.name), )
    file_info.short_description = _('file info')
    file_info.allow_tags = True

    def determine_file_type(self, name):
        """
        >>> t = MediaFileBase()
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
        for type_key, type_name, type_test in self.filetypes:
            if type_test(name):
                return type_key
        return self.filetypes[-1][0]

    def save(self, *args, **kwargs):
        if not self.id and not self.created:
            self.created = datetime.now()

        self.type = self.determine_file_type(self.file.name)

        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except (OSError, IOError, ValueError), e:
                logging.error("Unable to read file size for %s: %s", self, e)

        super(MediaFileBase, self).save(*args, **kwargs)

# ------------------------------------------------------------------------
MediaFileBase.register_filetypes(
        # Should we be using imghdr.what instead of extension guessing?
        ('image', _('Image'), lambda f: re.compile(r'\.(bmp|jpe?g|jp2|jxr|gif|png|tiff?)$', re.IGNORECASE).search(f)),
        ('video', _('Video'), lambda f: re.compile(r'\.(mov|m[14]v|mp4|avi|mpe?g|qt|ogv|wmv)$', re.IGNORECASE).search(f)),
        ('audio', _('Audio'), lambda f: re.compile(r'\.(au|mp3|m4a|wma|oga|ram|wav)$', re.IGNORECASE).search(f)),
        ('pdf', _('PDF document'), lambda f: f.lower().endswith('.pdf')),
        ('swf', _('Flash'), lambda f: f.lower().endswith('.swf')),
        ('txt', _('Text'), lambda f: f.lower().endswith('.txt')),
        ('rtf', _('Rich Text'), lambda f: f.lower().endswith('.rtf')),
        ('doc', _('Microsoft Word'), lambda f: re.compile(r'\.docx?$', re.IGNORECASE).search(f)),
        ('xls', _('Microsoft Excel'), lambda f: re.compile(r'\.xlsx?$', re.IGNORECASE).search(f)),
        ('ppt', _('Microsoft PowerPoint'), lambda f: re.compile(r'\.pptx?$', re.IGNORECASE).search(f)),
        ('other', _('Binary'), lambda f: True), # Must be last
    )

# ------------------------------------------------------------------------
class MediaFile(MediaFileBase):
    @classmethod
    def register_extension(cls, register_fn):
        register_fn(cls, MediaFileAdmin)
        pass

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
class MediaFileTranslation(Translation(MediaFile)):
    caption = models.CharField(_('caption'), max_length=200)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        verbose_name = _('media file translation')
        verbose_name_plural = _('media file translations')

    def __unicode__(self):
        return self.caption

#-------------------------------------------------------------------------
class MediaFileTranslationInline(admin.StackedInline):
    model   = MediaFileTranslation
    max_num = len(django_settings.LANGUAGES)

class MediaFileAdmin(admin.ModelAdmin):
    date_hierarchy    = 'created'
    inlines           = [MediaFileTranslationInline]
    list_display      = ['__unicode__', 'file_type', 'copyright', 'file_info', 'formatted_file_size', 'created']
    list_filter       = ['type', 'categories']
    list_per_page     = 25
    search_fields     = ['copyright', 'file', 'translations__caption']
    filter_horizontal = ("categories",)

    def queryset(self, request):
        qs = super(MediaFileAdmin, self).queryset(request)

        # FIXME: This is an ugly hack but it avoids 1-3 queries per *FILE*
        # retrieving the translation information
        if django_settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            qs = qs.extra(
                select = {
                    'preferred_translation':
                        """SELECT caption FROM medialibrary_mediafiletranslation
                        WHERE medialibrary_mediafiletranslation.parent_id = medialibrary_mediafile.id
                        ORDER BY
                            language_code = %s DESC,
                            language_code = %s DESC,
                            LENGTH(language_code) DESC
                        LIMIT 1
                        """
                },
                select_params = (translation.get_language(), django_settings.LANGUAGE_CODE)
            )
        return qs

#-------------------------------------------------------------------------

