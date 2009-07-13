# coding=utf-8

from datetime import datetime, timedelta
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist
from django.template.defaultfilters import slugify
from django.test import TestCase

from feincms.content.contactform.models import ContactFormContent
from feincms.content.file.models import FileContent
from feincms.content.image.models import ImageContent
from feincms.content.raw.models import RawContent
from feincms.content.richtext.models import RichTextContent
from feincms.content.video.models import VideoContent

from feincms.models import Region, Template, Base
from feincms.module.blog.models import Entry
from feincms.module.medialibrary.models import Category, MediaFile
from feincms.module.page.models import Page
from feincms.templatetags import feincms_tags
from feincms.translations import short_language_code
from feincms.utils import collect_dict_values, get_object, prefill_entry_list, \
    prefilled_attribute


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
            Region('region2', 'region2 title'),
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


Page.register_extensions('datepublisher', 'navigation', 'seo', 'symlinks',
                         'titles', 'translations', 'seo')

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

    def create_page(self, title='Test page', parent='', **kwargs):
        dic = {
            'title': title,
            'slug': kwargs.get('slug', slugify(title)),
            'parent': parent,
            'template_key': 'base',
            'publication_date_0': '2009-01-01',
            'publication_date_1': '00:00:00',
            'initial-publication_date_0': '2009-01-01',
            'initial-publication_date_1': '00:00:00',
            'language': 'en',
            }
        dic.update(kwargs)
        return self.client.post('/admin/page/page/add/', dic)

    def create_default_page_set(self):
        self.login()
        self.create_page()
        return self.create_page('Test child page', 1)

    def test_01_tree_editor(self):
        self.login()
        assert self.client.get('/admin/page/page/').status_code == 200

    def test_02_add_page(self):
        self.login()
        self.assertRedirects(self.create_page(title='Test page ' * 10, slug='test-page'),
                             '/admin/page/page/')
        assert Page.objects.count() == 1
        self.assertContains(self.client.get('/admin/page/page/'), '…')

    def test_03_item_editor(self):
        self.login()
        self.assertRedirects(self.create_page(_continue=1), '/admin/page/page/1/')
        assert self.client.get('/admin/page/page/1/').status_code == 200

    def test_03_add_another(self):
        self.login()
        self.assertRedirects(self.create_page(_addanother=1), '/admin/page/page/add/')

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

    def test_06_tree_editor_save(self):
        self.create_default_page_set()

        self.client.post('/admin/page/page/', {
            '__cmd': 'save_tree',
            'tree': '[[2, 0, 1], [1, 2, 0]]',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        page = Page.objects.get(pk=1)
        self.assertEqual(page.get_absolute_url(), '/test-child-page/test-page/')

    def test_07_tree_editor_delete(self):
        self.create_default_page_set()

        self.client.post('/admin/page/page/', {
            '__cmd': 'delete_item',
            'item_id': 2,
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertRaises(Page.DoesNotExist, lambda: Page.objects.get(pk=2))

    def test_07_tree_editor_invalid_ajax(self):
        self.login()
        self.assertContains(self.client.post('/admin/page/page/', {
            '__cmd': 'notexists',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest'),
            'Oops. AJAX request not understood.')

    def is_published(self, url, should_be=True):
        try:
            self.client.get(url)
        except TemplateDoesNotExist, e:
            if should_be:
                if e.args != ('feincms_base.html',):
                    raise
            else:
                if e.args != ('404.html',):
                    raise

    def test_08_publishing(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        self.is_published(page.get_absolute_url(), should_be=False)

        page.active = True
        page.save()
        self.is_published(page.get_absolute_url(), should_be=True)

        old_publication = page.publication_date
        page.publication_date = datetime.now() + timedelta(days=1)
        page.save()
        self.is_published(page.get_absolute_url(), should_be=False)

        page.publication_date = old_publication
        page.publication_end_date = datetime.now() - timedelta(days=1)
        page.save()
        self.is_published(page.get_absolute_url(), should_be=False)

        page.publication_end_date = datetime.now() + timedelta(days=1)
        page.save()
        self.is_published(page.get_absolute_url(), should_be=True)

    def create_pagecontent(self, page):
         return self.client.post('/admin/page/page/1/', {
            'title': page.title,
            'slug': page.slug,
            #'parent': page.parent_id, # this field is excluded from the form
            'template_key': page.template_key,
            'publication_date_0': '2009-01-01',
            'publication_date_1': '00:00:00',
            'initial-publication_date_0': '2009-01-01',
            'initial-publication_date_1': '00:00:00',
            'language': 'en',

            'rawcontent-TOTAL_FORMS': 1,
            'rawcontent-INITIAL_FORMS': 0,

            'rawcontent-0-parent': 1,
            'rawcontent-0-region': 'main',
            'rawcontent-0-ordering': 0,
            'rawcontent-0-text': 'This is some example content',

            'mediafilecontent-TOTAL_FORMS': 1,
            'mediafilecontent-INITIAL_FORMS': 0,

            'mediafilecontent-0-parent': 1,
            'mediafilecontent-0-position': 'block',

            'imagecontent-TOTAL_FORMS': 1,
            'imagecontent-INITIAL_FORMS': 0,

            'imagecontent-0-parent': 1,
            'imagecontent-0-position': 'default',
            })

    def test_09_pagecontent(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        response = self.create_pagecontent(page)
        self.assertRedirects(response, '/admin/page/page/')
        self.assertEqual(page.content.main[0].__class__.__name__, 'RawContent')

        page2 = Page.objects.get(pk=2)
        page2.symlinked_page = page
        self.assertEqual(page2.content.main[0].__class__.__name__, 'RawContent')

        self.assertEqual(len(page2.content.main), 1)
        self.assertEqual(len(page2.content.sidebar), 0)
        self.assertEqual(len(page2.content.nonexistant_region), 0)

    def test_10_mediafilecontent(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        self.create_pagecontent(page)

        path = os.path.join(settings.MEDIA_ROOT, 'somefile.jpg')
        f = open(path, 'wb')
        f.write('blabla')
        f.close()

        category = Category.objects.create(title='Category', parent=None)
        category2 = Category.objects.create(title='Something', parent=category)

        self.assertEqual(unicode(category2), 'Category - Something')

        mediafile = MediaFile.objects.create(file='somefile.jpg')
        mediafile.categories = [category]
        mediafile.translations.create(caption='something',
            language_code='%s-ha' % short_language_code())

        page.mediafilecontent_set.create(
            mediafile=mediafile,
            region='main',
            position='block',
            ordering=1)

        mf = page.content.main[1].mediafile

        self.assertEqual(mf.translation.caption, 'something')
        self.assertEqual(mf.translation.short_language_code(), short_language_code())
        self.assertNotEqual(mf.get_absolute_url(), '')
        self.assertEqual(unicode(mf), 'something (somefile.jpg / 6 bytes)')
        self.assertEqual(mf.file_type(), 'Image')

        os.unlink(path)

        self.client.get('/admin/page/page/1/')

        self.assertEqual(page.content.main[1].render(), """<div class="image">\n    <img src="/media/somefile.jpg" alt="something" />\n    <span class="caption">something</span>\n    \n</div>\n""")

    def test_11_translations(self):
        self.create_default_page_set()

        page1 = Page.objects.get(pk=1)
        self.assertEqual(len(page1.available_translations()), 0)

        page1 = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)

        page2.language = 'de'
        page2.translation_of = page1
        page2.save()

        self.assertEqual(len(page2.available_translations()), 1)
        self.assertEqual(len(page1.available_translations()), 1)

    def test_12_titles(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)

        self.assertEqual(page.page_title, page.title)
        self.assertEqual(page.content_title, page.title)

        page._content_title = 'Something\nawful'
        page._page_title = 'Hello world'
        page.save()

        self.assertEqual(page.page_title, 'Hello world')
        self.assertEqual(page.content_title, 'Something')
        self.assertEqual(page.content_subtitle, 'awful')

        page._content_title = 'Only one line'
        self.assertEqual(page.content_title, 'Only one line')
        self.assertEqual(page.content_subtitle, '')

        page._content_title = ''
        self.assertEqual(page.content_title, page.title)
        self.assertEqual(page.content_subtitle, '')

    def test_13_inheritance(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        page.rawcontent_set.create(
            region='sidebar',
            ordering=0,
            text='Something')

        page2 = Page.objects.get(pk=2)

        self.assertEqual(page2.content.sidebar[0].render(), 'Something')

    def test_14_richtext(self):
        # only create the content type to test the item editor
        # customization hooks
        tmp = Page._feincms_content_types[:]
        Page.create_content_type(RichTextContent, regions=('notexists',))
        Page._feincms_content_types = tmp

    def test_15_frontend_editing(self):
        self.create_default_page_set()
        page = Page.objects.get(pk=1)
        self.create_pagecontent(page)

        assert self.client.get('/admin/page/page/1/rawcontent/1/').status_code == 200
        assert self.client.post('/admin/page/page/1/rawcontent/1/', {
            'rawcontent-text': 'blablabla',
            }).status_code == 200

        self.assertEqual(page.content.main[0].render(), 'blablabla')
        self.assertEqual(feincms_tags.feincms_frontend_editing(page, {}), u'')

    def test_16_template_tags(self):
        self.create_default_page_set()
        page = Page.objects.get(pk=1)
        self.create_pagecontent(page)

        self.assertEqual(feincms_tags.feincms_render_region(page, 'main', {}),
                         'This is some example content')
        self.assertEqual(feincms_tags.feincms_render_content(page.content.main[0], {}),
                         'This is some example content')


Entry.register_extensions('seo', 'translations', 'seo')
class BlogTestCase(TestCase):
    def setUp(self):
        u = User(username='test', is_active=True, is_staff=True, is_superuser=True)
        u.set_password('test')
        u.save()

        Entry.register_regions(('main', 'Main region'))
        Entry.prefilled_categories = prefilled_attribute('categories')
        Entry.prefilled_rawcontent_set = prefilled_attribute('rawcontent_set')

    def login(self):
        assert self.client.login(username='test', password='test')

    def create_entry(self):
        entry = Entry.objects.create(
            published=True,
            title='Something',
            slug='something',
            language='en')

        entry.rawcontent_set.create(
            region='main',
            ordering=0,
            text='Something awful')

    def test_01_prefilled_attributes(self):
        self.create_entry()

        objects = prefill_entry_list(Entry.objects.published(), 'rawcontent_set', 'categories')

        self.assertEqual(len(objects[0].prefilled_categories), 0)
        self.assertEqual(len(objects[0].prefilled_rawcontent_set), 1)
        self.assertEqual(unicode(objects[0]), 'Something')

        self.login()
        assert self.client.get('/admin/blog/entry/').status_code == 200
        assert self.client.get('/admin/blog/entry/1/').status_code == 200

