# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``rebuild_mptt``
---------------------

``rebuild_mptt`` rebuilds your mptt pointers. Only use in emergencies.
"""

from django.core.management.base import NoArgsCommand

from feincms.module.page.models import Page

class Command(NoArgsCommand):
    help = "Run this manually to rebuild your mptt pointers. Only use in emergencies."

    def handle_noargs(self, **options):
        print "Rebuilding MPTT pointers for Page"
        Page.tree.rebuild()
