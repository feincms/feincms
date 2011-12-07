# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  Created by Martin J. Laubach on 2011-12-07
#  Copyright (c) 2011 Martin J. Laubach. All rights reserved.
#
# ------------------------------------------------------------------------

from __future__ import absolute_import

from datetime import datetime
import zipfile
import os
import time

from django.template.defaultfilters import slugify
from django.utils import simplejson
from django.contrib import messages
from django.utils.translation import ungettext, ugettext_lazy as _
from django.conf import settings as django_settings

from .models import Category, MediaFile, MediaFileTranslation

# ------------------------------------------------------------------------
export_magic = 'feincms-export-01'

# ------------------------------------------------------------------------
def import_zipfile(category_id, data):
    category = None
    if category_id:
        category = Category.objects.get(pk=int(category_id))

    z = zipfile.ZipFile(data)

    # Peek into zip file to find out whether it contains meta information
    is_export_file = False
    info = {}
    try:
        info = simplejson.loads(z.comment)
        if info['export_magic'] == export_magic:
            is_export_file = True
    except:
        pass

     # If meta information, do we need to create any categories?
    # Also build translation map for category ids.
    category_id_map = {}
    if is_export_file:
        for cat in sorted(info.get('categories', []), key=lambda k: k.get('level', 999)):
            new_cat, created = Category.objects.get_or_create(slug=cat['slug'], title=cat['title'])
            category_id_map[cat['id']] = new_cat
            if created and cat.get('parent', 0):
                parent_cat = category_id_map.get(cat.get('parent', 0), None)
                if parent_cat:
                    new_cat.parent = parent_cat
                    new_cat.save()

    count = 0
    for zi in z.infolist():
        if not zi.filename.endswith('/'):
            from django.core.files.base import ContentFile

            bname = os.path.basename(zi.filename)
            if bname and not bname.startswith(".") and "." in bname:
                fname, ext = os.path.splitext(bname)
                target_fname = slugify(fname) + ext.lower()

                info = {}
                if is_export_file:
                    info = simplejson.loads(zi.comment)

                mf = MediaFile()
                mf.file.save(target_fname, ContentFile(z.read(zi.filename)))
                mf.copyright = info.get('copyright', None)
                mf.save()

                if category:
                    mf.categories.add(category)

                found_metadata = False
                if is_export_file:
                    try:
                        for tr in info['translations']:
                            found_metadata = True
                            mt = MediaFileTranslation()
                            mt.parent = mf
                            mt.language_code = tr['lang']
                            mt.caption       = tr['caption']
                            mt.description   = tr.get('description', None)
                            mt.save()

                        # Add categories
                        mf.categories = (category_id_map[cat_id] for cat_id in info.get('categories', []))
                    except Exception, e:
                        print e

                if not found_metadata:
                    mt = MediaFileTranslation()
                    mt.parent  = mf
                    mt.caption = fname.replace('_', ' ')
                    mt.save()

                mf.purge_translation_cache()
                count += 1

    return count

# ------------------------------------------------------------------------
def export_zipfile(site, queryset):
    now  = datetime.today()
    zip_name = "export_%s_%04d%02d%02d.zip" % (slugify(site.domain), now.year, now.month, now.day)

    zip_data = open(os.path.join(django_settings.MEDIA_ROOT, zip_name), "w")
    zip_file = zipfile.ZipFile(zip_data, 'w', allowZip64=True)

    # Save the used categories in the zip file's global comment
    used_categories = set()
    for mf in queryset:
        for cat in mf.categories.all():
            used_categories.update(cat.path_list())

    info = { 'export_magic': export_magic,
             'categories': [ { 'id': cat.id, 'title': cat.title, 'slug': cat.slug, 'parent': cat.parent_id or 0, 'level': len(cat.path_list()) } for cat in used_categories ],
            }
    zip_file.comment = simplejson.dumps(info)

    for mf in queryset:
        ctime = time.localtime(os.stat(mf.file.path).st_ctime)
        info = simplejson.dumps({
            'copyright': mf.copyright,
            'categories': [ cat.id for cat in mf.categories.all() ],
            'translations': [
                { 'lang': t.language_code, 'caption': t.caption, 'description': t.description }
                    for t in mf.translations.all() ],
            })

        with open(mf.file.path, "r") as file_data:
            zip_info = zipfile.ZipInfo(filename=mf.file.name, date_time=(ctime.tm_year, ctime.tm_mon, ctime.tm_mday, ctime.tm_hour, ctime.tm_min, ctime.tm_sec))
            zip_info.comment = info
            zip_file.writestr(zip_info, file_data.read())

    return zip_name

# ------------------------------------------------------------------------
