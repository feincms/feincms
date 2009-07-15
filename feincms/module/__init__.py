# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from django.conf import settings
from django.utils.safestring import mark_safe

# ------------------------------------------------------------------------
def django_boolean_icon(field_val, alt_text=None, title=None):
    """
    Return HTML code for a nice representation of true/false.
    """

    # Origin: contrib/admin/templatetags/admin_list.py
    BOOLEAN_MAPPING = { True: 'yes', False: 'no', None: 'unknown' }
    alt_text = alt_text or BOOLEAN_MAPPING[field_val]
    if title is not None:
        title = 'title="%s" ' % title
    else:
        title = ''
    return mark_safe(u'<img src="%simg/admin/icon-%s.gif" alt="%s" %s/>' %
            (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], alt_text, title))

# ------------------------------------------------------------------------
