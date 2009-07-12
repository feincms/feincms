from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from feincms.content.contactform.models import ContactFormContent
from feincms.content.file.models import FileContent
from feincms.content.image.models import ImageContent
from feincms.content.raw.models import RawContent
from feincms.content.richtext.models import RichTextContent
from feincms.content.video.models import VideoContent

from feincms.models import Region, Template, Base
from feincms.utils import collect_dict_values, get_object


class TranslationsTest(TestCase):
    def test_short_language_code(self):
        # this is quite stupid, but it's the first time I do something
        # with TestCase

        import feincms.translations
        import doctest

        doctest.testmod(feincms.translations)


class ModelsTest(TestCase):
    def test_region(self):
        # Creation should not fail

        r = Region('region', 'region title')
        t = Template('base template', 'base.html', (
            ('region', 'region title'),
            ))

        # I'm not sure whether this test tests anything at all
        self.assertEqual(r.key, t.regions[0].key)


class UtilsTest(TestCase):
    def test_get_object(self):
        from feincms.utils import get_object

        self.assertRaises(AttributeError, lambda: get_object('feincms.does_not_exist'))
        self.assertRaises(ImportError, lambda: get_object('feincms.does_not_exist.fn'))

        self.assertEqual(get_object, get_object('feincms.utils.get_object'))

    def test_collect_dict_values(self):
        from feincms.utils import collect_dict_values

        self.assertEqual({'a': [1, 2], 'b': [3]},
            collect_dict_values([('a', 1), ('a', 2), ('b', 3)]))


class ExampleCMSBase(Base):
    pass

ExampleCMSBase.register_regions(('region', 'region title'))

class CMSBaseTest(TestCase):
    def test_01_simple_content_type_creation(self):
        ExampleCMSBase.create_content_type(ContactFormContent)
        ExampleCMSBase.create_content_type(FileContent)
        ExampleCMSBase.create_content_type(ImageContent,
            POSITION_CHOICES=(('left', 'left'),))
        ExampleCMSBase.create_content_type(RawContent)
        ExampleCMSBase.create_content_type(RichTextContent)
        ExampleCMSBase.create_content_type(VideoContent)

    def test_02_rsscontent_creation(self):
        # this test resides in its own method because the required feedparser
        # module is not available everywhere
        from feincms.content.rss.models import RSSContent
        ExampleCMSBase.create_content_type(RSSContent)

    def test_03_double_creation(self):
        # creating a content type twice is forbidden
        self.assertRaises(ImproperlyConfigured,
            lambda: ExampleCMSBase.create_content_type(RawContent))

    def test_04_mediafilecontent_creation(self):
        # the medialibrary needs to be enabled, otherwise this test fails

        from feincms.content.medialibrary.models import MediaFileContent

        # We use the convenience method here which has defaults for
        # POSITION_CHOICES
        MediaFileContent.default_create_content_type(ExampleCMSBase)
