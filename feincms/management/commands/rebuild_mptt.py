# ------------------------------------------------------------------------
# coding=utf-8
# $Id$
# ------------------------------------------------------------------------

from django.core.management.base import NoArgsCommand
from django.db import transaction

from feincms.module.page.models import Page

class Command(NoArgsCommand):
    help = "Run this manually to rebuild your mptt pointers. Only use in emergencies."

    @staticmethod
    def seq(start = 1):
        """
        Returns an ever-increasing stream of numbers. The starting point can
        be freely defined.
        """
        while True:
            yield start
            start += 1


    @transaction.commit_manually
    def handle_noargs(self, **options):
        print "Rebuilding MPTT pointers for Page"
        root = 1
        changes = set()
        for page in Page.objects.filter(parent__isnull=True).order_by('tree_id'):
            print "  Processing subtree %d at %s" % ( page.tree_id, page.slug )

            page.tree_id = root # Renumber tree_id for good measure

            self.renumber_mptt_tree(page, self.seq(1))

            root += 1
            transaction.commit()

    def renumber_mptt_tree(self, obj, edge_count):
        obj.lft = edge_count.next()
        for c in obj.children.order_by('lft', 'rght').all():
            self.renumber_mptt_tree(c, edge_count)
        obj.rght = edge_count.next()
        obj.save()