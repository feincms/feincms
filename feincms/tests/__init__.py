# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

import os

if os.environ.get('FEINCMS_RUN_TESTS'):
    from .test_cms import *
    from .test_page import *
    from .test_stuff import *

# ------------------------------------------------------------------------
