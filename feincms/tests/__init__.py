# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

import os

if os.environ.get('FEINCMS_RUN_TESTS'):
    from .cms_tests import *
    from .page_tests import *
    from .tests import *

# ------------------------------------------------------------------------
