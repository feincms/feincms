"""Compatibility shims."""
import sys


# Python 2/3 compatiibility.
# From http://lucumr.pocoo.org/2013/5/21/porting-to-python-3-redux/
PY2 = sys.version_info[0] == 2
if not PY2:
    text_type = str
    unichr = chr
else:
    text_type = unicode
    unichr = unichr
