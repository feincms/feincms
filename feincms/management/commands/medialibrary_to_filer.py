from __future__ import absolute_import, unicode_literals

from django.core.files import File as DjangoFile
from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

from feincms.contents import MediaFileContent, FileContent, ImageContent
from feincms.module.medialibrary.models import MediaFile
from feincms.module.page.models import Page

from filer.models import File, Image


PageMediaFileContent = Page.content_type_for(MediaFileContent)
PageFileContent = Page.content_type_for(FileContent)
PageImageContent = Page.content_type_for(ImageContent)


assert (PageMediaFileContent and PageFileContent and PageImageContent),\
    'Not all required models available'


class Command(NoArgsCommand):
    help = "Migrate the medialibrary and contents to django-filer"

    def handle_noargs(self, **options):
        user = User.objects.order_by('pk')[0]

        count = MediaFile.objects.count()

        for i, mediafile in enumerate(MediaFile.objects.order_by('pk')):
            model = Image if mediafile.type == 'image' else File
            content_model = PageImageContent if mediafile.type == 'image' else PageFileContent  # noqa

            filerfile = model.objects.create(
                owner=user,
                original_filename=mediafile.file.name,
                file=DjangoFile(
                    mediafile.file.file,
                    name=mediafile.file.name,
                ),
            )

            contents = PageMediaFileContent.objects.filter(mediafile=mediafile)

            for content in contents:
                content_model.objects.create(
                    parent=content.parent,
                    region=content.region,
                    ordering=content.ordering,
                    type=content.type,
                    mediafile=filerfile,
                )

                content.delete()

            if not i % 10:
                self.stdout.write('%s / %s files\n' % (i, count))

        self.stdout.write('%s / %s files\n' % (count, count))
