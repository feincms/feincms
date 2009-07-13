from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import slugify
from django.test import TestCase

from feincms.content.contactform.models import ContactFormContent
from feincms.content.file.models import FileContent
from feincms.content.image.models import ImageContent
from feincms.content.raw.models import RawContent
from feincms.content.richtext.models import RichTextContent
from feincms.content.video.models import VideoContent

from feincms.models import Region, Template, Base
from feincms.module.page.models import Page
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


class PageModelTest(TestCase):
    def test_01_extensions(self):
        Page.register_extensions('datepublisher', 'navigation', 'seo', 'symlinks',
                                 'titles', 'translations')


class PagesTestCase(TestCase):
    def setUp(self):
        u = User(username='test', is_active=True, is_staff=True, is_superuser=True)
        u.set_password('test')
        u.save()

        Page.register_templates({
                'key': 'base',
                'title': 'Standard template',
                'path': 'feincms_base.html',
                'regions': (
                    ('main', 'Main content area'),
                    ('sidebar', 'Sidebar', 'inherited'),
                    ),
                })

    def login(self):
        assert self.client.login(username='test', password='test')

    def create_page(self, title='Test page', parent=''):
        return self.client.post('/admin/page/page/add/', {
            'title': title,
            'slug': slugify(title),
            'parent': parent,
            'template_key': 'base',
            })

    def create_default_page_set(self):
        self.login()
        self.create_page()
        return self.create_page('Test child page', 1)

    def test_01_tree_editor(self):
        self.login()
        assert self.client.get('/admin/page/page/').status_code == 200

    def test_02_add_page(self):
        self.login()
        self.assertRedirects(self.create_page(), '/admin/page/page/')
        assert Page.objects.count() == 1

    def test_03_item_editor(self):
        self.login()
        self.create_page()
        assert self.client.get('/admin/page/page/1/').status_code == 200

    def test_04_add_child(self):
        response = self.create_default_page_set()
        self.assertRedirects(response, '/admin/page/page/')
        assert Page.objects.count() == 2

        page = Page.objects.get(pk=2)
        self.assertEqual(page.get_absolute_url(), '/test-page/test-child-page/')

    def test_05_override_url(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        page.override_url = '/something/'
        page.save()

        page2 = Page.objects.get(pk=2)
        self.assertEqual(page2.get_absolute_url(), '/something/test-child-page/')

        page.override_url = '/'
        page.save()
        page2 = Page.objects.get(pk=2)
        self.assertEqual(page2.get_absolute_url(), '/test-child-page/')

