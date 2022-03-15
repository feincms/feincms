import os

from django.conf import settings
from django.core.management.base import BaseCommand

from feincms.module.medialibrary.models import MediaFile


class Command(BaseCommand):
    help = "Prints all orphaned files in the `media/medialibrary` folder"

    def handle(self, **options):
        mediafiles = list(MediaFile.objects.values_list("file", flat=True))

        root_len = len(settings.MEDIA_ROOT)
        medialib_path = os.path.join(settings.MEDIA_ROOT, "medialibrary")

        for base, dirs, files in os.walk(medialib_path):
            for f in files:
                if base.startswith(settings.MEDIA_ROOT):
                    base = base[root_len:]
                full = os.path.join(base, f)
                if full not in mediafiles:
                    self.stdout.write(full)
