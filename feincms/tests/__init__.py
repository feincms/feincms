import sys

from feincms import settings

try:
    any
except NameError:
    from feincms.compat import c_any as any


def is_feincms_test():
    return any('feincms' in arg for arg in sys.argv[2:])


if settings.FEINCMS_RUN_TESTS or is_feincms_test():
    from feincms.tests.base import *
