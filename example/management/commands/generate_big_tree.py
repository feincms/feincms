# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from django.core.management.base import NoArgsCommand

from feincms.module.page.models import Page


class Command(NoArgsCommand):
    help = (
        "Run this command to generate a big tree for performance testing"
        " purposes.")

    def handle_noargs(self, **options):
        parents = [None] * 5

        Page.objects.all().delete()

        for i1 in range(5):
            parents[0] = Page.objects.create(
                title='Page %s' % (i1,),
            )

            for i2 in range(5):
                parents[1] = Page.objects.create(
                    title='Page %s.%s' % (i1, i2),
                    parent=parents[0],
                )

                for i3 in range(5):
                    parents[2] = Page.objects.create(
                        title='Page %s.%s.%s' % (i1, i2, i3),
                        parent=parents[1],
                    )

                    for i4 in range(5):
                        parents[3] = Page.objects.create(
                            title='Page %s.%s.%s.%s' % (i1, i2, i3, i4),
                            parent=parents[2],
                        )
