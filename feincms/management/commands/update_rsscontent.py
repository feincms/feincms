from django.core.management.base import NoArgsCommand

from feincms.content.rss.models import RSSContent

class Command(NoArgsCommand):
    help = "Run this as a cronjob."

    def handle_noargs(self, **options):
        # find all concrete content types of RSSContent
        for cls in RSSContent._feincms_content_models:
            for content in cls.objects.all():
                content.cache_content()

