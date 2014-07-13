from __future__ import absolute_import, unicode_literals

import os

from django.core.management.base import NoArgsCommand
from django.utils.encoding import force_text

from feincms.module.medialibrary.models import MediaFile


class Command(NoArgsCommand):
    help = "Prints all orphaned files in the `media/medialibrary` folder"

    def handle_noargs(self, **options):
        mediafiles = list(MediaFile.objects.values_list('file', flat=True))

        # TODO make this smarter, and take MEDIA_ROOT into account
        for base, dirs, files in os.walk('media/medialibrary'):
            for f in files:
                full = os.path.join(base[6:], f)
                if force_text(full) not in mediafiles:
                    self.stdout.write(os.path.join(base, f))
