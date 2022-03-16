# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
"""
``rebuild_mptt``
---------------------

``rebuild_mptt`` rebuilds your mptt pointers. Only use in emergencies.
"""


from django.core.management.base import BaseCommand

from feincms.module.page.models import Page


class Command(BaseCommand):
    help = "Run this manually to rebuild your mptt pointers. Only use in emergencies."

    def handle_noargs(self, **options):
        self.handle(**options)

    def handle(self, **options):
        self.stdout.write("Rebuilding MPTT pointers for Page")
        Page._tree_manager.rebuild()
