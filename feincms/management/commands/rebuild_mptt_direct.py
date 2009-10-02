# encoding: utf-8

import logging

from django.core.management.base import NoArgsCommand
from django.db import transaction, connection, backend

from feincms.module.page.models import Page

class Command(NoArgsCommand):
    help = "Manually rebuild MPTT hierarchy - should only be used to repair damaged databases"

    @transaction.commit_manually
    def handle_noargs(self, **options):
        logging.info("Rebuilding all MPTT trees")
        try:
            rebuild()
            transaction.commit()
        except backend.DatabaseError:
            logging.exception("Unable to rebuild MPTT tree due to exception: rolling back all changes")
            transaction.rollback()

# TODO: Move this into utils and add a post-migrate/syncdb signal handler
# which can automatically rebuild after a fixture load?

# Based heavily on the code from http://code.google.com/p/django-mptt/issues/detail?id=13
qn = connection.ops.quote_name

def rebuild():
    """
    Rebuilds whole tree in database using `parent` link.
    """
    opts = Page._meta
    tree = Page.tree

    cursor = connection.cursor()
    cursor.execute('UPDATE %(table)s SET %(left)s = 0, %(right)s = 0, %(level)s = 0, %(tree_id)s = 0' % {
        'table': qn(opts.db_table),
        'left': qn(opts.get_field(tree.left_attr).column),
        'right': qn(opts.get_field(tree.right_attr).column),
        'level': qn(opts.get_field(tree.level_attr).column),
        'tree_id': qn(opts.get_field(tree.tree_id_attr).column)
    })

    cursor.execute('SELECT %(id_col)s FROM %(table)s WHERE %(parent_col)s is NULL %(orderby)s' % {
        'id_col': qn(opts.pk.column),
        'table': qn(opts.db_table),
        'parent_col': qn(opts.get_field(tree.parent_attr).column),
        'orderby': 'ORDER BY ' + ', '.join([qn(field) for field in opts.order_insertion_by]) if opts.order_insertion_by else ''
    })

    idx = 0
    for (pk, ) in cursor.fetchall():
        idx += 1
        _rebuild_helper(pk, 1, idx)
    transaction.commit_unless_managed()

def _rebuild_helper(pk, left, tree_id, level=0):
    opts = Page._meta
    tree = Page.tree
    right = left + 1

    cursor = connection.cursor()
    cursor.execute('SELECT %(id_col)s FROM %(table)s WHERE %(parent_col)s = %(parent)d %(orderby)s' % {
        'id_col': qn(opts.pk.column),
        'table': qn(opts.db_table),
        'parent_col': qn(opts.get_field(tree.parent_attr).column),
        'parent': pk,
        'orderby': 'ORDER BY ' + ', '.join([qn(field) for field in opts.order_insertion_by]) if opts.order_insertion_by else ''
    })

    for (child_id, ) in cursor.fetchall():
        right = _rebuild_helper(child_id, right, tree_id, level+1)

    cursor.execute("""
        UPDATE %(table)s
        SET
            %(left_col)s = %(left)d,
            %(right_col)s = %(right)d,
            %(level_col)s = %(level)d,
            %(tree_id_col)s = %(tree_id)d
        WHERE
            %(pk_col)s = %(pk)s
    """ % {
        'table': qn(opts.db_table),
        'pk_col': qn(opts.pk.column),
        'left_col': qn(opts.get_field(tree.left_attr).column),
        'right_col': qn(opts.get_field(tree.right_attr).column),
        'level_col': qn(opts.get_field(tree.level_attr).column),
        'tree_id_col': qn(opts.get_field(tree.tree_id_attr).column),
        'pk': pk,
        'left': left,
        'right': right,
        'level': level,
        'tree_id': tree_id
    })

    return right + 1
