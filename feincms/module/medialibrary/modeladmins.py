# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import os

from django import forms
from django.conf import settings as django_settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.sites.models import Site
from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.defaultfilters import filesizeformat
from django.utils.safestring import mark_safe
from django.utils.translation import ungettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from feincms.extensions import ExtensionModelAdmin
from feincms.translations import admin_translationinline, lookup_translations
from feincms.utils import shorten_string

from .models import Category, MediaFileTranslation
from .forms import MediaCategoryAdminForm, MediaFileAdminForm
from .thumbnail import admin_thumbnail
from .zip import import_zipfile


# -----------------------------------------------------------------------
class CategoryAdmin(admin.ModelAdmin):
    form = MediaCategoryAdminForm
    list_display = ['path']
    list_filter = ['parent']
    list_per_page = 25
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}


# ------------------------------------------------------------------------
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

            message = ungettext(
                'Successfully added %(count)d media file to %(category)s.',
                'Successfully added %(count)d media files to %(category)s.',
                count) % {'count': count, 'category': category}
            modeladmin.message_user(request, message)
            return HttpResponseRedirect(request.get_full_path())
    if 'cancel' in request.POST:
        return HttpResponseRedirect(request.get_full_path())

    if not form:
        form = AddCategoryForm(initial={
            '_selected_action': request.POST.getlist(
                admin.ACTION_CHECKBOX_NAME),
        })

    return render_to_response('admin/medialibrary/add_to_category.html', {
        'mediafiles': queryset,
        'category_form': form,
        'opts': modeladmin.model._meta,
    }, context_instance=RequestContext(request))


assign_category.short_description = _('Add selected media files to category')


# -------------------------------------------------------------------------
def save_as_zipfile(modeladmin, request, queryset):
    from .zip import export_zipfile

    site = Site.objects.get_current()
    try:
        zip_name = export_zipfile(site, queryset)
        messages.info(request, _("ZIP file exported as %s") % zip_name)
    except Exception as e:
        messages.error(request, _("ZIP file export failed: %s") % str(e))
        return

    return HttpResponseRedirect(
        os.path.join(django_settings.MEDIA_URL, zip_name))


save_as_zipfile.short_description = _(
    'Export selected media files as zip file')


# ------------------------------------------------------------------------
class MediaFileAdmin(ExtensionModelAdmin):
    form = MediaFileAdminForm

    save_on_top = True
    date_hierarchy = 'created'
    inlines = [admin_translationinline(MediaFileTranslation)]
    list_display = [
        'admin_thumbnail', '__str__', 'file_info', 'formatted_created']
    list_display_links = ['__str__']
    list_filter = ['type', 'categories']
    list_per_page = 25
    search_fields = ['copyright', 'file', 'translations__caption']
    filter_horizontal = ("categories",)
    actions = [assign_category, save_as_zipfile]

    def get_urls(self):
        from django.conf.urls import patterns, url

        urls = super(MediaFileAdmin, self).get_urls()
        my_urls = patterns(
            '',
            url(
                r'^mediafile-bulk-upload/$',
                self.admin_site.admin_view(MediaFileAdmin.bulk_upload),
                {},
                name='mediafile_bulk_upload',
            ),
        )

        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['categories'] = Category.objects.order_by('title')
        return super(MediaFileAdmin, self).changelist_view(
            request, extra_context=extra_context)

    def admin_thumbnail(self, obj):
        image = admin_thumbnail(obj)
        if image:
            return mark_safe("""
                <a href="%(url)s" target="_blank">
                    <img src="%(image)s" alt="" />
                </a>""" % {
                'url': obj.file.url,
                'image': image}
            )
        return ''
    admin_thumbnail.short_description = _('Preview')
    admin_thumbnail.allow_tags = True

    def formatted_file_size(self, obj):
        return filesizeformat(obj.file_size)
    formatted_file_size.short_description = _("file size")
    formatted_file_size.admin_order_field = 'file_size'

    def formatted_created(self, obj):
        return obj.created.strftime("%Y-%m-%d")
    formatted_created.short_description = _("created")
    formatted_created.admin_order_field = 'created'

    def file_type(self, obj):
        t = obj.filetypes_dict[obj.type]
        if obj.type == 'image':
            # get_image_dimensions is expensive / slow if the storage is not
            # local filesystem (indicated by availability the path property)
            try:
                obj.file.path
            except NotImplementedError:
                return t
            try:
                d = get_image_dimensions(obj.file.file)
                if d:
                    t += " %d&times;%d" % (d[0], d[1])
            except (IOError, ValueError) as e:
                t += " (%s)" % e
        return t
    file_type.admin_order_field = 'type'
    file_type.short_description = _('file type')
    file_type.allow_tags = True

    def file_info(self, obj):
        """
        Method for showing the file name in admin.

        Note: This also includes a hidden field that can be used to extract
        the file name later on, this can be used to access the file name from
        JS, like for example a TinyMCE connector shim.
        """
        return (
            '<input type="hidden" class="medialibrary_file_path"'
            ' name="_media_path_%d" value="%s" id="_refkey_%d" />'
            ' %s <br />%s, %s'
        ) % (
            obj.id,
            obj.file.name,
            obj.id,
            shorten_string(os.path.basename(obj.file.name), max_length=40),
            self.file_type(obj),
            self.formatted_file_size(obj),
        )
    file_info.admin_order_field = 'file'
    file_info.short_description = _('file info')
    file_info.allow_tags = True

    @staticmethod
    @csrf_protect
    @permission_required('medialibrary.add_mediafile')
    def bulk_upload(request):
        if request.method == 'POST' and 'data' in request.FILES:
            try:
                count = import_zipfile(
                    request.POST.get('category'),
                    request.POST.get('overwrite', False),
                    request.FILES['data'])
                messages.info(request, _("%d files imported") % count)
            except Exception as e:
                messages.error(request, _("ZIP import failed: %s") % e)
        else:
            messages.error(request, _("No input file given"))

        return HttpResponseRedirect(
            reverse('admin:medialibrary_mediafile_changelist'))

    def queryset(self, request):
        return super(MediaFileAdmin, self).queryset(request).transform(
            lookup_translations())

    def save_model(self, request, obj, form, change):
        obj.purge_translation_cache()
        return super(MediaFileAdmin, self).save_model(
            request, obj, form, change)

    def to_field_allowed(self, request, to_field):
        """
        This is a workaround for issue #552 which will raise a security
        exception in the media select popup with django 1.6.6+.
        According to the release notes, this should be fixed by the
        yet (2014-09-22) unreleased 1.6.8, 1.5.11.

        Details: https://code.djangoproject.com/ticket/23329#comment:11
        """

        if to_field == 'id':
            return True

        return super(MediaFileAdmin, self).to_field_allowed(request, to_field)

# ------------------------------------------------------------------------
