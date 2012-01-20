"""
``update_rsscontent``
---------------------

``update_rsscontent`` should be run as a cronjob when the ``RSSContent``
content type is used -- the content type itself does not update the
feed by itself.
"""

from django.core.management.base import BaseCommand

from feincms.content.rss.models import RSSContent

class Command(BaseCommand):
    help = "Run this as a cronjob."

    def handle(self, date_format='', *args, **options):
        # find all concrete content types of RSSContent
        for cls in RSSContent._feincms_content_models:
            for content in cls.objects.all():
                if date_format:
                    content.cache_content(date_format=date_format)
                else:
                    content.cache_content()
