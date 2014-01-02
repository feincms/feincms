# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  Created by Martin J. Laubach on 2011-12-07
#  Copyright (c) 2011 Martin J. Laubach. All rights reserved.
#
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import json
import zipfile
import os
import time

from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from django.template.defaultfilters import slugify
from django.utils import timezone

from .models import Category, MediaFile, MediaFileTranslation


# ------------------------------------------------------------------------
export_magic = 'feincms-export-01'


# ------------------------------------------------------------------------
def import_zipfile(category_id, overwrite, data):
    """
    Import a collection of media files from a zip file.

    category_id: if set, the pk of a Category that all uploaded
        files will have added (eg. cathegory "newly uploaded files")
    overwrite: attempt to overwrite existing files. This might
        not work with non-trivial storage handlers
    """
    category = None
    if category_id:
        category = Category.objects.get(pk=int(category_id))

    z = zipfile.ZipFile(data)

    # Peek into zip file to find out whether it contains meta information
    is_export_file = False
    info = {}
    try:
        info = json.loads(z.comment)
        if info['export_magic'] == export_magic:
            is_export_file = True
    except:
        pass

    # If meta information, do we need to create any categories?
    # Also build translation map for category ids.
    category_id_map = {}
    if is_export_file:
        for cat in sorted(
                info.get('categories', []),
                key=lambda k: k.get('level', 999)):
            new_cat, created = Category.objects.get_or_create(
                slug=cat['slug'],
                title=cat['title'])
            category_id_map[cat['id']] = new_cat
            if created and cat.get('parent', 0):
                parent_cat = category_id_map.get(cat.get('parent', 0), None)
                if parent_cat:
                    new_cat.parent = parent_cat
                    new_cat.save()

    count = 0
    for zi in z.infolist():
        if not zi.filename.endswith('/'):
            bname = os.path.basename(zi.filename)
            if bname and not bname.startswith(".") and "." in bname:
                fname, ext = os.path.splitext(bname)
                wanted_dir = os.path.dirname(zi.filename)
                target_fname = slugify(fname) + ext.lower()

                info = {}
                if is_export_file:
                    info = json.loads(zi.comment)

                mf = None
                if overwrite:
                    full_path = os.path.join(wanted_dir, target_fname)
                    try:
                        mf = MediaFile.objects.get(file=full_path)
                        mf.file.delete(save=False)
                    except MediaFile.DoesNotExist:
                        mf = None

                if mf is None:
                    mf = MediaFile()
                if overwrite:
                    mf.file.field.upload_to = wanted_dir
                mf.copyright = info.get('copyright', '')
                mf.file.save(
                    target_fname,
                    ContentFile(z.read(zi.filename)),
                    save=False)
                mf.save()

                found_metadata = False
                if is_export_file:
                    try:
                        for tr in info['translations']:
                            found_metadata = True
                            mt, mt_created =\
                                MediaFileTranslation.objects.get_or_create(
                                    parent=mf, language_code=tr['lang'])
                            mt.caption = tr['caption']
                            mt.description = tr.get('description', None)
                            mt.save()

                        # Add categories
                        mf.categories = (
                            category_id_map[cat_id]
                            for cat_id in info.get('categories', []))
                    except Exception:
                        pass

                if not found_metadata:
                    mt = MediaFileTranslation()
                    mt.parent = mf
                    mt.caption = fname.replace('_', ' ')
                    mt.save()

                if category:
                    mf.categories.add(category)

                count += 1

    return count


# ------------------------------------------------------------------------
def export_zipfile(site, queryset):
    now = timezone.now()
    zip_name = "export_%s_%04d%02d%02d.zip" % (
        slugify(site.domain), now.year, now.month, now.day)

    zip_data = open(os.path.join(django_settings.MEDIA_ROOT, zip_name), "w")
    zip_file = zipfile.ZipFile(zip_data, 'w', allowZip64=True)

    # Save the used categories in the zip file's global comment
    used_categories = set()
    for mf in queryset:
        for cat in mf.categories.all():
            used_categories.update(cat.path_list())

    info = {
        'export_magic': export_magic,
        'categories': [{
            'id': cat.id,
            'title': cat.title,
            'slug': cat.slug,
            'parent': cat.parent_id or 0,
            'level': len(cat.path_list()),
        } for cat in used_categories],
    }
    zip_file.comment = json.dumps(info)

    for mf in queryset:
        ctime = time.localtime(os.stat(mf.file.path).st_ctime)
        info = json.dumps({
            'copyright': mf.copyright,
            'categories': [cat.id for cat in mf.categories.all()],
            'translations': [{
                'lang': t.language_code,
                'caption': t.caption,
                'description': t.description,
            } for t in mf.translations.all()],
        })

        with open(mf.file.path, "r") as file_data:
            zip_info = zipfile.ZipInfo(
                filename=mf.file.name,
                date_time=(
                    ctime.tm_year,
                    ctime.tm_mon,
                    ctime.tm_mday,
                    ctime.tm_hour,
                    ctime.tm_min,
                    ctime.tm_sec))
            zip_info.comment = info
            zip_file.writestr(zip_info, file_data.read())

    return zip_name

# ------------------------------------------------------------------------
