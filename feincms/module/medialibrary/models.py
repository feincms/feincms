# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

from datetime import datetime
import logging
import os
import re

# Try to import PIL in either of the two ways it can end up installed.
try:
    from PIL import Image
except ImportError:
    import Image

from django import forms
from django.conf import settings as django_settings
from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.defaultfilters import filesizeformat, slugify
from django.utils.safestring import mark_safe
from django.utils.translation import ungettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from feincms import settings
from feincms.models import ExtensionsMixin
from feincms.templatetags import feincms_thumbnail
from feincms.translations import (TranslatedObjectMixin, Translation,
    TranslatedObjectManager, admin_translationinline, lookup_translations)

# ------------------------------------------------------------------------
class CategoryManager(models.Manager):
    """
    Simple manager which exists only to supply ``.select_related("parent")``
    on querysets since we can't even __unicode__ efficiently without it.
    """
    def get_query_set(self):
        return super(CategoryManager, self).get_query_set().select_related("parent")

# ------------------------------------------------------------------------
class Category(models.Model):
    """
    These categories are meant primarily for organizing media files in the
    library.
    """

    title = models.CharField(_('title'), max_length=200)
    parent = models.ForeignKey('self', blank=True, null=True,
        related_name='children', limit_choices_to={'parent__isnull': True},
        verbose_name=_('parent'))

    slug = models.SlugField(_('slug'), max_length=150)

    class Meta:
        ordering = ['parent__title', 'title']
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    objects = CategoryManager()

    def __unicode__(self):
        if self.parent_id:
            return u'%s - %s' % (self.parent.title, self.title)

        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super(Category, self).save(*args, **kwargs)

    def path_list(self):
        if self.parent is None:
            return [ self ]
        p = self.parent.path_list()
        p.append(self)
        return p

    def path(self):
        return ' - '.join((f.title for f in self.path_list()))

class CategoryAdmin(admin.ModelAdmin):
    list_display      = ['path']
    list_filter       = ['parent']
    list_per_page     = 25
    search_fields     = ['title']
    prepopulated_fields = { 'slug': ('title',), }

# ------------------------------------------------------------------------
class MediaFileBase(models.Model, ExtensionsMixin, TranslatedObjectMixin):
    """
    Abstract media file class. Includes the :class:`feincms.models.ExtensionsMixin`
    because of the (handy) extension mechanism.
    """

    file = models.FileField(_('file'), max_length=255, upload_to=settings.FEINCMS_MEDIALIBRARY_UPLOAD_TO)
    type = models.CharField(_('file type'), max_length=12, editable=False, choices=())
    created = models.DateTimeField(_('created'), editable=False, default=datetime.now)
    copyright = models.CharField(_('copyright'), max_length=200, blank=True)
    file_size  = models.IntegerField(_("file size"), blank=True, null=True, editable=False)

    categories = models.ManyToManyField(Category, verbose_name=_('categories'),
                                        blank=True, null=True)
    categories.category_filter = True

    class Meta:
        abstract = True
        ordering = ['-created']
        verbose_name = _('media file')
        verbose_name_plural = _('media files')

    objects = TranslatedObjectManager()

    filetypes = [ ]
    filetypes_dict = { }

    def formatted_file_size(self):
        return filesizeformat(self.file_size)
    formatted_file_size.short_description = _("file size")
    formatted_file_size.admin_order_field = 'file_size'

    def formatted_created(self):
        return self.created.strftime("%Y-%m-%d")
    formatted_created.short_description = _("created")
    formatted_created.admin_order_field = 'created'

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

    def __init__(self, *args, **kwargs):
        super(MediaFileBase, self).__init__(*args, **kwargs)
        if self.file:
            self._original_file_name = self.file.name

    def __unicode__(self):
        trans = None

        try:
            trans = self.translation
        except models.ObjectDoesNotExist:
            pass
        except AttributeError:
            pass

        if trans:
            trans = unicode(trans)
            if trans.strip():
                return trans
        return os.path.basename(self.file.name)

    def get_absolute_url(self):
        return self.file.url

    def file_type(self):
        t = self.filetypes_dict[self.type]
        if self.type == 'image':
            # get_image_dimensions is expensive / slow if the storage is not local filesystem (indicated by availability the path property)
            try:
                self.file.path
            except NotImplementedError:
                return t
            try:
                from django.core.files.images import get_image_dimensions
                d = get_image_dimensions(self.file.file)
                if d: t += " %d&times;%d" % ( d[0], d[1] )
            except IOError, e:
                t += " (%s)" % e.strerror
        return t
    file_type.admin_order_field = 'type'
    file_type.short_description = _('file type')
    file_type.allow_tags = True

    def file_info(self):
        """
        Method for showing the file name in admin.

        Note: This also includes a hidden field that can be used to extract
        the file name later on, this can be used to access the file name from
        JS, like for example a TinyMCE connector shim.
        """
        from feincms.utils import shorten_string
        return u'<input type="hidden" class="medialibrary_file_path" name="_media_path_%d" value="%s" id="_refkey_%d" /> %s <br />%s, %s' % (
                self.id,
                self.file.name,
                self.id,
                shorten_string(os.path.basename(self.file.name), max_length=40),
                self.file_type(),
                self.formatted_file_size(),
                )
    file_info.admin_order_field = 'file'
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
        if self.file:
            try:
                self.file_size = self.file.size
            except (OSError, IOError, ValueError), e:
                logging.error("Unable to read file size for %s: %s", self, e)

        # Try to detect things that are not really images
        if self.type == 'image':
            try:
                try:
                    image = Image.open(self.file)
                except (OSError, IOError):
                    image = Image.open(self.file.path)

                # Rotate image based on exif data.
                if image:
                    try:
                        exif = image._getexif()
                    except (AttributeError, IOError):
                        exif = False
                    # PIL < 1.1.7 chokes on JPEGs with minimal EXIF data and
                    # throws a KeyError deep in its guts.
                    except KeyError:
                        exif = False

                    if exif:
                        orientation = exif.get(274)
                        rotation = 0
                        if orientation == 3:
                            rotation = 180
                        elif orientation == 6:
                            rotation = 270
                        elif orientation == 8:
                            rotation = 90
                        if rotation:
                            image = image.rotate(rotation)
                            image.save(self.file.path)
            except (OSError, IOError), e:
                self.type = self.determine_file_type('***') # It's binary something

        if getattr(self, '_original_file_name', None):
            if self.file.name != self._original_file_name:
                self.file.storage.delete(self._original_file_name)

        super(MediaFileBase, self).save(*args, **kwargs)
        self.purge_translation_cache()

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
        ('zip', _('Zip archive'), lambda f: f.lower().endswith('.zip')),
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

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
class MediaFileTranslation(Translation(MediaFile)):
    """
    Translated media file caption and description.
    """

    caption = models.CharField(_('caption'), max_length=200)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        verbose_name = _('media file translation')
        verbose_name_plural = _('media file translations')

    def __unicode__(self):
        return self.caption

#-------------------------------------------------------------------------
def admin_thumbnail(obj):
    if obj.type == 'image':
        image = None
        try:
            image = feincms_thumbnail.thumbnail(obj.file.name, '100x100')
        except:
            pass

        if image:
            return mark_safe(u"""
                <a href="%(url)s" target="_blank">
                    <img src="%(image)s" alt="" />
                </a>""" % {
                    'url': obj.file.url,
                    'image': image,})
    return ''
admin_thumbnail.short_description = _('Preview')
admin_thumbnail.allow_tags = True

#-------------------------------------------------------------------------
def assign_category(modeladmin, request, queryset):
    class AddCategoryForm(forms.Form):
        _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
        category = forms.ModelChoiceField(Category.objects.all())

    form = None
    if 'apply' in request.POST:
        form = AddCategoryForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']

            count = 0
            for mediafile in queryset:
                category.mediafile_set.add(mediafile)
                count += 1

            message = ungettext('Successfully added %(count)d media file to %(category)s.',
                                'Successfully added %(count)d media files to %(category)s.',
                                count) % {'count':count, 'category':category}
            modeladmin.message_user(request, message)
            return HttpResponseRedirect(request.get_full_path())
    if 'cancel' in request.POST:
        return HttpResponseRedirect(request.get_full_path())

    if not form:
        form = AddCategoryForm(initial={
            '_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME),
            })

    return render_to_response('admin/medialibrary/add_to_category.html', {
        'mediafiles': queryset,
        'category_form': form,
        }, context_instance=RequestContext(request))

assign_category.short_description = _('Add selected media files to category')

#-------------------------------------------------------------------------
def save_as_zipfile(modeladmin, request, queryset):
    from .zip import export_zipfile

    site = Site.objects.get_current()
    try:
        zip_name = export_zipfile(site, queryset)
        messages.info(request, _("ZIP file exported as %s") % zip_name)
    except Exception, e:
        messages.error(request, _("ZIP file export failed: %s") % str(e))

    return HttpResponseRedirect(os.path.join(django_settings.MEDIA_URL, zip_name))

save_as_zipfile.short_description = _('Export selected media files as zip file')

# ------------------------------------------------------------------------
class MediaFileAdminForm(forms.ModelForm):
    class Meta:
        model = MediaFile

    def __init__(self, *args, **kwargs):
        super(MediaFileAdminForm, self).__init__(*args, **kwargs)
        if settings.FEINCMS_MEDIAFILE_OVERWRITE and self.instance.id:
            self.original_name = self.instance.file.name

            def gen_fname(instance, filename):
                self.instance.file.storage.delete(self.original_name)
                return self.original_name
            self.instance.file.field.generate_filename = gen_fname

    def clean_file(self):
        if settings.FEINCMS_MEDIAFILE_OVERWRITE and hasattr(self, 'original_name'):
            new_base, new_ext = os.path.splitext(self.cleaned_data['file'].name)
            old_base, old_ext = os.path.splitext(self.original_name)

            if new_ext.lower() != old_ext.lower():
                raise forms.ValidationError(_("Cannot overwrite with different file type (attempt to overwrite a %(old_ext)s with a %(new_ext)s)") % { 'old_ext': old_ext, 'new_ext': new_ext })

        return self.cleaned_data['file']

# -----------------------------------------------------------------------
class MediaFileAdmin(admin.ModelAdmin):
    save_on_top       = True
    form              = MediaFileAdminForm
    date_hierarchy    = 'created'
    inlines           = [admin_translationinline(MediaFileTranslation)]
    list_display      = [admin_thumbnail, '__unicode__', 'file_info', 'formatted_created']
    list_display_links = ['__unicode__']
    list_filter       = ['type', 'categories']
    list_per_page     = 25
    search_fields     = ['copyright', 'file', 'translations__caption']
    filter_horizontal = ("categories",)
    actions           = [assign_category, save_as_zipfile]

    def get_urls(self):
        from django.conf.urls.defaults import url, patterns

        urls = super(MediaFileAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^mediafile-bulk-upload/$', self.admin_site.admin_view(MediaFileAdmin.bulk_upload), {}, name='mediafile_bulk_upload')
            )

        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['categories'] = Category.objects.order_by('title')
        return super(MediaFileAdmin, self).changelist_view(request, extra_context=extra_context)

    @staticmethod
    @csrf_protect
    @permission_required('medialibrary.add_mediafile')
    def bulk_upload(request):
        from .zip import import_zipfile

        if request.method == 'POST' and 'data' in request.FILES:
            try:
                count = import_zipfile(request.POST.get('category'), request.POST.get('overwrite', False), request.FILES['data'])
                messages.info(request, _("%d files imported") % count)
            except Exception, e:
                messages.error(request, _("ZIP import failed: %s") % str(e))
        else:
            messages.error(request, _("No input file given"))

        return HttpResponseRedirect(reverse('admin:medialibrary_mediafile_changelist'))

    def queryset(self, request):
        return super(MediaFileAdmin, self).queryset(request).transform(lookup_translations())

    def save_model(self, request, obj, form, change):
        obj.purge_translation_cache()
        return super(MediaFileAdmin, self).save_model(request, obj, form, change)


#-------------------------------------------------------------------------
