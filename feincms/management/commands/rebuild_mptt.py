# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
``rebuild_mptt``
---------------------

``rebuild_mptt`` rebuilds your mptt pointers. Only use in emergencies.
"""

from __future__ import absolute_import, unicode_literals

from django.core.management.base import NoArgsCommand

from feincms.module.page.models import Page


class Command(NoArgsCommand):
    help = (
        "Run this manually to rebuild your mptt pointers. Only use in"
        " emergencies.")

    def handle_noargs(self, **options):
        self.stdout.write("Rebuilding MPTT pointers for Page")
        Page._tree_manager.rebuild()
