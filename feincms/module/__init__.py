# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from django.conf import settings
from django.utils.safestring import mark_safe

# ------------------------------------------------------------------------
def django_boolean_image_url(on_or_off):
    # Origin: contrib/admin/templatetags/admin_list.py
    BOOLEAN_MAPPING = { True: 'yes', False: 'no', None: 'unknown' }
    path = '%simg/admin/icon-%s.gif' % \
            (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[on_or_off])
    return path
            
def django_boolean_icon(field_val, alt_text='', title=None):
    """
    Return HTML code for a nice representation of true/false.
    """

    if title is not None:
        title = 'title="%s" ' % title
    else:
        title = ''
    return mark_safe(u'<img src="%s" alt="%s" %s/>' %
            (django_boolean_image_url(field_val), alt_text, title))

# ------------------------------------------------------------------------
