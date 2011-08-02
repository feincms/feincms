# coding=utf-8

from datetime import datetime, timedelta
import os

from django import forms, template
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.sites.models import Site
from django.http import Http404, HttpResponseBadRequest
from django.template import TemplateDoesNotExist
from django.template.defaultfilters import slugify
from django.test import TestCase

from feincms import settings as feincms_settings
from feincms.content.application.models import ApplicationContent, _empty_reverse_cache, reverse
from feincms.content.contactform.models import ContactFormContent, ContactForm
from feincms.content.file.models import FileContent
from feincms.content.image.models import ImageContent
from feincms.content.raw.models import RawContent
from feincms.content.richtext.models import RichTextContent
from feincms.content.video.models import VideoContent

from feincms.context_processors import add_page_if_missing
from feincms.models import Region, Template, Base, ContentProxy
from feincms.module.blog.models import Entry
from feincms.module.medialibrary.models import Category, MediaFile
from feincms.module.page.models import Page
from feincms.templatetags import feincms_tags
from feincms.translations import short_language_code
from feincms.utils import collect_dict_values, get_object, prefill_entry_list, \
    prefilled_attribute


class Empty(object):
    """
    Helper class to use as request substitute (or whatever)
    """

    pass

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
        self.assertEqual(unicode(r), 'region title')


class UtilsTest(TestCase):
    def test_get_object(self):
        self.assertRaises(AttributeError, lambda: get_object('feincms.does_not_exist'))
        self.assertRaises(ImportError, lambda: get_object('feincms.does_not_exist.fn'))

        self.assertEqual(get_object, get_object('feincms.utils.get_object'))

    def test_collect_dict_values(self):
        self.assertEqual({'a': [1, 2], 'b': [3]},
            collect_dict_values([('a', 1), ('a', 2), ('b', 3)]))


class ExampleCMSBase(Base):
    pass

ExampleCMSBase.register_regions(('region', 'region title'), ('region2', 'region2 title'))


class ExampleCMSBase2(Base):
        pass

ExampleCMSBase2.register_regions(('region', 'region title'),
        ('region2', 'region2 title'))


class CMSBaseTest(TestCase):
    def test_01_simple_content_type_creation(self):
        self.assertEqual(ExampleCMSBase.content_type_for(FileContent), None)

        ExampleCMSBase.create_content_type(ContactFormContent)
        ExampleCMSBase.create_content_type(FileContent, regions=('region2',))

        # no POSITION_CHOICES, should raise
        self.assertRaises(ImproperlyConfigured,
                          lambda: ExampleCMSBase.create_content_type(ImageContent))

        ExampleCMSBase.create_content_type(RawContent)
        ExampleCMSBase.create_content_type(RichTextContent)

        # test creating a cotent with arguments, but no initialize_type classmethod
        ExampleCMSBase.create_content_type(VideoContent, arbitrary_arg='arbitrary_value')

        # content_type_for should return None if it does not have a subclass registered
        self.assertEqual(ExampleCMSBase.content_type_for(Empty), None)

        self.assertTrue('filecontent' not in dict(ExampleCMSBase.template.regions[0].content_types).keys())
        self.assertTrue('filecontent' in dict(ExampleCMSBase.template.regions[1].content_types).keys())

    def test_02_rsscontent_creation(self):
        # this test resides in its own method because the required feedparser
        # module is not available everywhere
        from feincms.content.rss.models import RSSContent
        type = ExampleCMSBase.create_content_type(RSSContent)
        obj = type()

        self.assertTrue('yahoo' not in obj.render())

        obj.link = 'http://rss.news.yahoo.com/rss/topstories'
        obj.cache_content(save=False)

        self.assertTrue('yahoo' in obj.render())

    #Creating a content type twice isn't forbidden anymore
    #def test_03_double_creation(self):
    #    # creating a content type twice is forbidden
    #    self.assertRaises(ImproperlyConfigured,
    #        lambda: ExampleCMSBase.create_content_type(RawContent))

    def test_04_mediafilecontent_creation(self):
        # the medialibrary needs to be enabled, otherwise this test fails

        from feincms.content.medialibrary.models import MediaFileContent

        # no POSITION_CHOICES, should raise
        self.assertRaises(ImproperlyConfigured,
                          lambda: ExampleCMSBase.create_content_type(MediaFileContent))

    def test_05_non_abstract_content_type(self):
        # Should not be able to create a content type from a non-abstract base type
        class TestContentType(models.Model):
            pass

        self.assertRaises(ImproperlyConfigured,
            lambda: ExampleCMSBase.create_content_type(TestContentType))

    def test_06_videocontent(self):
        type = ExampleCMSBase.content_type_for(VideoContent)
        obj = type()
        obj.video = 'http://www.youtube.com/watch?v=zmj1rpzDRZ0'

        self.assertTrue('x-shockwave-flash' in obj.render())

        self.assertEqual(getattr(type, 'arbitrary_arg'), 'arbitrary_value')

        obj.video = 'http://www.example.com/'

        self.assertTrue(obj.video in obj.render())

    def test_07_default_render_method(self):
        class SomethingElse(models.Model):
            class Meta:
                abstract = True

            def render_region(self):
                return 'hello'

        type = ExampleCMSBase.create_content_type(SomethingElse)
        obj = type()
        self.assertRaises(NotImplementedError, lambda: obj.render())

        obj.region = 'region'
        self.assertEqual(obj.render(), 'hello')

    def test_08_creating_two_content_types_in_same_application(self):
        ExampleCMSBase.create_content_type(RawContent)
        ct = ExampleCMSBase.content_type_for(RawContent)
        self.assertEqual(ct._meta.db_table, 'tests_examplecmsbase_rawcontent')

        ExampleCMSBase2.create_content_type(RawContent, class_name='RawContent2')
        ct2 = ExampleCMSBase2.content_type_for(RawContent)
        self.assertEqual(ct2._meta.db_table, 'tests_examplecmsbase2_rawcontent2')



Page.register_extensions('datepublisher', 'navigation', 'seo', 'symlinks',
                         'titles', 'translations', 'seo', 'changedate',
                         'ct_tracker')
Page.create_content_type(ContactFormContent, form=ContactForm)
Page.create_content_type(FileContent)
Page.register_request_processors(Page.etag_request_processor)
Page.register_response_processors(Page.etag_response_processor)
Page.register_response_processors(Page.debug_sql_queries_response_processor())


class PagesTestCase(TestCase):
    def setUp(self):
        u = User(username='test', is_active=True, is_staff=True, is_superuser=True)
        u.set_password('test')
        u.save()


        self.site_1 = Site.objects.all()[0]

        Page.register_templates({
                'key': 'base',
                'title': 'Standard template',
                'path': 'feincms_base.html',
                'regions': (
                    ('main', 'Main content area'),
                    ('sidebar', 'Sidebar', 'inherited'),
                    ),
                }, {
                'key': 'theother',
                'title': 'This actually exists',
                'path': 'base.html',
                'regions': (
                    ('main', 'Main content area'),
                    ('sidebar', 'Sidebar', 'inherited'),
                    ),
                })
        feincms_settings.FEINCMS_USE_CACHE = True

    def login(self):
        self.assertTrue(self.client.login(username='test', password='test'))

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
            'site': self.site_1.id,

            'rawcontent_set-TOTAL_FORMS': 0,
            'rawcontent_set-INITIAL_FORMS': 0,
            'rawcontent_set-MAX_NUM_FORMS': 10,

            'mediafilecontent_set-TOTAL_FORMS': 0,
            'mediafilecontent_set-INITIAL_FORMS': 0,
            'mediafilecontent_set-MAX_NUM_FORMS': 10,

            'imagecontent_set-TOTAL_FORMS': 0,
            'imagecontent_set-INITIAL_FORMS': 0,
            'imagecontent_set-MAX_NUM_FORMS': 10,

            'contactformcontent_set-TOTAL_FORMS': 0,
            'contactformcontent_set-INITIAL_FORMS': 0,
            'contactformcontent_set-MAX_NUM_FORMS': 10,

            'filecontent_set-TOTAL_FORMS': 0,
            'filecontent_set-INITIAL_FORMS': 0,
            'filecontent_set-MAX_NUM_FORMS': 10,

            'applicationcontent_set-TOTAL_FORMS': 0,
            'applicationcontent_set-INITIAL_FORMS': 0,
            'applicationcontent_set-MAX_NUM_FORMS': 10,
            }
        dic.update(kwargs)
        return self.client.post('/admin/page/page/add/', dic)

    def create_default_page_set(self):
        self.login()
        self.create_page()
        return self.create_page('Test child page', 1)

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

    def test_01_tree_editor(self):
        self.login()
        self.assertEqual(self.client.get('/admin/page/page/').status_code, 200)

        self.assertRedirects(self.client.get('/admin/page/page/?anything=anything'),
                             '/admin/page/page/?e=1')

    def test_02_add_page(self):
        self.login()
        self.assertRedirects(self.create_page(title='Test page ' * 10, slug='test-page'),
                             '/admin/page/page/')
        self.assertEqual(Page.objects.count(), 1)
        self.assertContains(self.client.get('/admin/page/page/'), '…')

    def test_03_item_editor(self):
        self.login()
        self.assertRedirects(self.create_page(_continue=1), '/admin/page/page/1/')
        self.assertEqual(self.client.get('/admin/page/page/1/').status_code, 200)
        self.is_published('/admin/page/page/42/', should_be=False)

    def test_03_add_another(self):
        self.login()
        self.assertRedirects(self.create_page(_addanother=1), '/admin/page/page/add/')

    def test_04_add_child(self):
        response = self.create_default_page_set()
        self.assertRedirects(response, '/admin/page/page/')
        self.assertEqual(Page.objects.count(), 2)

        page = Page.objects.get(pk=2)
        self.assertEqual(page.get_absolute_url(), '/test-page/test-child-page/')

        page.active = True
        page.in_navigation = True
        page.save()

        # page2 inherited the inactive flag from the toplevel page
        self.assertContains(self.client.get('/admin/page/page/'), 'inherited')

        page1 = Page.objects.get(pk=1)
        page1.active = True
        page1.save()

        self.assertEqual(len(self.client.get('/admin/page/page/').content.split('checked="checked"')), 4)

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

        # This goes through feincms.views.base.handler instead of the applicationcontent handler
        self.is_published('/', False)
        page.active = True
        page.template_key = 'theother'
        page.save()
        self.is_published('/', True)

    def test_06_tree_editor_save(self):
        self.create_default_page_set()

        page1 = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)

        page3 = Page.objects.create(title='page3', slug='page3', parent=page2)
        page4 = Page.objects.create(title='page4', slug='page4', parent=page1)
        page5 = Page.objects.create(title='page5', slug='page5', parent=None)

        self.assertEqual(page3.get_absolute_url(), '/test-page/test-child-page/page3/')
        self.assertEqual(page4.get_absolute_url(), '/test-page/page4/')
        self.assertEqual(page5.get_absolute_url(), '/page5/')

        self.client.post('/admin/page/page/', {
            '__cmd': 'move_node',
            'position': 'last-child',
            'cut_item': '1',
            'pasted_on': '5',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(Page.objects.get(pk=1).get_absolute_url(),
                         '/page5/test-page/')
        self.assertEqual(Page.objects.get(pk=5).get_absolute_url(),
                         '/page5/')
        self.assertEqual(Page.objects.get(pk=3).get_absolute_url(),
                         '/page5/test-page/test-child-page/page3/')

    def test_07_tree_editor_toggle_boolean(self):
        self.create_default_page_set()

        self.assertEqual(Page.objects.get(pk=1).in_navigation, False)

        self.assertContains(self.client.post('/admin/page/page/', {
            '__cmd': 'toggle_boolean',
            'item_id': 1,
            'attr': 'in_navigation',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest'),
            r'checked=\"checked\"')
        self.assertEqual(Page.objects.get(pk=1).in_navigation, True)
        self.assertNotContains(self.client.post('/admin/page/page/', {
            '__cmd': 'toggle_boolean',
            'item_id': 1,
            'attr': 'in_navigation',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest'),
            'checked="checked"')
        self.assertEqual(Page.objects.get(pk=1).in_navigation, False)

        self.assertTrue(isinstance(self.client.post('/admin/page/page/', {
            '__cmd': 'toggle_boolean',
            'item_id': 1,
            'attr': 'notexists',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest'), HttpResponseBadRequest))

    def test_07_tree_editor_invalid_ajax(self):
        self.login()
        self.assertContains(self.client.post('/admin/page/page/', {
            '__cmd': 'notexists',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest'),
            'Oops. AJAX request not understood.',
            status_code=400)

    def test_08_publishing(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)
        self.is_published(page.get_absolute_url(), should_be=False)
        self.is_published(page2.get_absolute_url(), should_be=False)

        page.active = True
        page.save()
        page2.active = True
        page2.save()
        self.is_published(page.get_absolute_url(), should_be=True)
        self.is_published(page2.get_absolute_url(), should_be=True)

        old_publication = page.publication_date
        page.publication_date = datetime.now() + timedelta(days=1)
        page.save()
        self.is_published(page.get_absolute_url(), should_be=False)

        # Should be not accessible because of its parent's inactivity
        self.is_published(page2.get_absolute_url(), should_be=False)

        page.publication_date = old_publication
        page.publication_end_date = datetime.now() - timedelta(days=1)
        page.save()
        self.is_published(page.get_absolute_url(), should_be=False)

        # Should be not accessible because of its parent's inactivity
        self.is_published(page2.get_absolute_url(), should_be=False)

        page.publication_end_date = datetime.now() + timedelta(days=1)
        page.save()
        self.is_published(page.get_absolute_url(), should_be=True)
        self.is_published(page2.get_absolute_url(), should_be=True)

    def create_pagecontent(self, page, **kwargs):
        data = {
            'title': page.title,
            'slug': page.slug,
            #'parent': page.parent_id, # this field is excluded from the form
            'template_key': page.template_key,
            'publication_date_0': '2009-01-01',
            'publication_date_1': '00:00:00',
            'initial-publication_date_0': '2009-01-01',
            'initial-publication_date_1': '00:00:00',
            'language': 'en',
            'site': self.site_1.id,

            'rawcontent_set-TOTAL_FORMS': 1,
            'rawcontent_set-INITIAL_FORMS': 0,
            'rawcontent_set-MAX_NUM_FORMS': 10,

            'rawcontent_set-0-parent': 1,
            'rawcontent_set-0-region': 'main',
            'rawcontent_set-0-ordering': 0,
            'rawcontent_set-0-text': 'This is some example content',

            'mediafilecontent_set-TOTAL_FORMS': 1,
            'mediafilecontent_set-INITIAL_FORMS': 0,
            'mediafilecontent_set-MAX_NUM_FORMS': 10,

            'mediafilecontent_set-0-parent': 1,
            'mediafilecontent_set-0-position': 'block',

            'imagecontent_set-TOTAL_FORMS': 1,
            'imagecontent_set-INITIAL_FORMS': 0,
            'imagecontent_set-MAX_NUM_FORMS': 10,

            'imagecontent_set-0-parent': 1,
            'imagecontent_set-0-position': 'default',

            'contactformcontent_set-TOTAL_FORMS': 1,
            'contactformcontent_set-INITIAL_FORMS': 0,
            'contactformcontent_set-MAX_NUM_FORMS': 10,

            'filecontent_set-TOTAL_FORMS': 1,
            'filecontent_set-INITIAL_FORMS': 0,
            'filecontent_set-MAX_NUM_FORMS': 10,

            'applicationcontent_set-TOTAL_FORMS': 1,
            'applicationcontent_set-INITIAL_FORMS': 0,
            'applicationcontent_set-MAX_NUM_FORMS': 10,
            }
        data.update(kwargs)

        return self.client.post('/admin/page/page/%s/' % page.pk, data)

    def test_09_pagecontent(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        response = self.create_pagecontent(page)
        self.assertRedirects(response, '/admin/page/page/')
        self.assertEqual(page.content.main[0].__class__.__name__, 'RawContent')

        page2 = Page.objects.get(pk=2)
        page2.symlinked_page = page

        # Test that all_of_type works correctly even before accessing
        # other content methods
        self.assertEqual(len(page2.content.all_of_type(RawContent)), 1)

        self.assertEqual(page2.content.main[0].__class__.__name__, 'RawContent')
        self.assertEqual(unicode(page2.content.main[0]),
                         'main on Test page, ordering 0')

        self.assertEqual(len(page2.content.main), 1)
        self.assertEqual(len(page2.content.sidebar), 0)
        self.assertEqual(len(page2.content.nonexistant_region), 0)

        self.assertTrue(isinstance(page2.content.media, forms.Media))

        self.assertEqual(len(page2.content.all_of_type(RawContent)), 1)
        self.assertEqual(len(page2.content.all_of_type((ImageContent,))), 0)
        self.assertEqual(len(page2.content.all_of_type([ImageContent])), 0)

    def test_10_mediafile_and_imagecontent(self):
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
        self.assertEqual(unicode(category), 'Category')

        mediafile = MediaFile.objects.create(file='somefile.jpg')
        mediafile.categories = [category]
        page.mediafilecontent_set.create(
            mediafile=mediafile,
            region='main',
            position='block',
            ordering=1)

        self.assertEqual(unicode(mediafile), 'somefile.jpg')

        mediafile.translations.create(caption='something',
            language_code='%s-ha' % short_language_code())

        self.assertTrue('something' in unicode(mediafile))

        mf = page.content.main[1].mediafile

        self.assertEqual(mf.translation.caption, 'something')
        self.assertEqual(mf.translation.short_language_code(), short_language_code())
        self.assertNotEqual(mf.get_absolute_url(), '')
        self.assertEqual(unicode(mf), 'something')
        self.assertEqual(unicode(mf.file_type()), u'Binary') # Ok, so it's not really an image...

        self.assertEqual(MediaFile.objects.only_language('de').count(), 0)
        self.assertEqual(MediaFile.objects.only_language('en').count(), 0)
        self.assertEqual(MediaFile.objects.only_language('%s-ha' % short_language_code()).count(),
                         1)

        self.assertTrue('%s-ha' % short_language_code() in mf.available_translations)

        os.unlink(path)

        # this should not raise
        self.client.get('/admin/page/page/1/')

        #self.assertTrue('alt="something"' in page.content.main[1].render()) Since it isn't an image

        page.imagecontent_set.create(image='somefile.jpg', region='main', position='default', ordering=2)
        page.filecontent_set.create(file='somefile.jpg', title='thetitle', region='main', ordering=3)

        # Reload page, reset _ct_inventory
        page = Page.objects.get(pk=page.pk)
        page._ct_inventory = None

        self.assertTrue('somefile.jpg' in page.content.main[2].render())
        self.assertTrue('<a href="/media/somefile.jpg">thetitle</a>' in page.content.main[3].render())

        page.mediafilecontent_set.update(mediafile=3)
        # this should not raise
        self.client.get('/admin/page/page/1/')

        field = MediaFile._meta.get_field('file')
        old = (field.upload_to, field.storage, field.generate_filename)
        from django.core.files.storage import FileSystemStorage
        MediaFile.reconfigure(upload_to=lambda: 'anywhere',
                              storage=FileSystemStorage(location='/wha/', base_url='/whe/'))
        mediafile = MediaFile.objects.get(pk=1)
        self.assertEqual(mediafile.file.url, '/whe/somefile.jpg')

        # restore settings
        (field.upload_to, field.storage, field.generate_filename) = old

        mediafile = MediaFile.objects.get(pk=1)
        self.assertEqual(mediafile.file.url, '/media/somefile.jpg')

    def test_11_translations(self):
        self.create_default_page_set()

        page1 = Page.objects.get(pk=1)
        self.assertEqual(len(page1.available_translations()), 0)

        page1 = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)

        page2.language = 'de'
        page2.save()

        self.assertEqual(len(page2.available_translations()), 0)

        page2.translation_of = page1
        page2.save()

        self.assertEqual(len(page2.available_translations()), 1)
        self.assertEqual(len(page1.available_translations()), 1)

        self.assertEqual(page1, page1.original_translation)
        self.assertEqual(page1, page2.original_translation)

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

    def test_13_inheritance_and_ct_tracker(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)
        page.rawcontent_set.create(
            region='sidebar',
            ordering=0,
            text='Something')
        page.rawcontent_set.create(
            region='main',
            ordering=0,
            text='Anything')

        page2 = Page.objects.get(pk=2)
        page2.rawcontent_set.create(
            region='main',
            ordering=0,
            text='Something else')
        page2.rawcontent_set.create(
            region='main',
            ordering=1,
            text='Whatever')

        # Set default, non-caching content proxy
        page2.content_proxy_class = ContentProxy

        if hasattr(self, 'assertNumQueries'):
        # 4 queries: Two to get the content types of page and page2, one to
            # fetch all ancestor PKs of page2 and one to materialize the RawContent
            # instances belonging to page's sidebar and page2's main.
            self.assertNumQueries(4, lambda: [page2.content.main, page2.content.sidebar])
            self.assertNumQueries(0, lambda: page2.content.sidebar[0].render())

        self.assertEqual(u''.join(c.render() for c in page2.content.main),
            'Something elseWhatever')
        self.assertEqual(page2.content.sidebar[0].render(), 'Something')

        page2 = Page.objects.get(pk=2)
        self.assertEqual(page2._ct_inventory, {})

        # Prime Django content type cache
        for ct in Page._feincms_content_types:
            ContentType.objects.get_for_model(ct)

        if hasattr(self, 'assertNumQueries'):
            # 5 queries: Two to get the content types of page and page2, one to
            # fetch all ancestor PKs of page2 and one to materialize the RawContent
            # instances belonging to page's sidebar and page2's main and a few
            # queries to update the pages _ct_inventory attributes:
            # - one update to update page2
            # - one update to clobber the _ct_inventory attribute of all descendants
            #   of page2
            self.assertNumQueries(5, lambda: [page2.content.main, page2.content.sidebar])
            self.assertNumQueries(0, lambda: page2.content.sidebar[0].render())

        self.assertEqual(page2.content.sidebar[0].render(), 'Something')

        # Reload, again, to test ct_tracker extension
        page2 = Page.objects.get(pk=2)

        if hasattr(self, 'assertNumQueries'):
            self.assertNumQueries(1, lambda: [page2.content.main, page2.content.sidebar])

        self.assertNotEqual(page2._ct_inventory, {})

    def test_14_richtext(self):
        # only create the content type to test the item editor
        # customization hooks
        tmp = Page._feincms_content_types[:]
        type = Page.create_content_type(RichTextContent, regions=('notexists',))
        Page._feincms_content_types = tmp

        from django.utils.safestring import SafeData
        obj = type()
        obj.text = 'Something'
        self.assertTrue(isinstance(obj.render(), SafeData))

    def test_15_frontend_editing(self):
        self.create_default_page_set()
        page = Page.objects.get(pk=1)
        self.create_pagecontent(page)

        # this should return a 404
        self.is_published('/admin/page/page/10|rawcontent|1/', should_be=False)
        self.is_published('/admin/page/page/1|rawcontent|10/', should_be=False)

        self.assertEqual(self.client.get('/admin/page/page/1|rawcontent|1/').status_code, 200)
        self.assertEqual(self.client.post('/admin/page/page/1|rawcontent|1/', {
            'rawcontent-text': 'blablabla',
            }).status_code, 200)

        self.assertEqual(page.content.main[0].render(), 'blablabla')
        self.assertEqual(feincms_tags.feincms_frontend_editing(page, {}), u'')

        request = Empty()
        request.session = {'frontend_editing': True}

        self.assertTrue('class="fe_box"' in\
            page.content.main[0].fe_render(request=request))

        self.assertFalse('class="fe_box"' in self.client.get(page.get_absolute_url() + '?frontend_editing=1').content)

    def test_16_template_tags(self):
        # Directly testing template tags doesn't make any sense since
        # feincms_render_* do not use simple_tag anymore
        pass

    def test_17_page_template_tags(self):
        self.create_default_page_set()

        page1 = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)

        page2.language = 'de'
        page2.translation_of = page1
        page2.active = True
        page2.in_navigation = True
        page2.save()

        page3 = Page.objects.create(parent=page2,
                                    title='page3',
                                    slug='page3',
                                    language='en',
                                    active=True,
                                    in_navigation=True,
                                    publication_date=datetime(2001, 1, 1),
                                    )

        # reload these two, their mptt attributes have changed
        page1 = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)

        context = template.Context({'feincms_page': page2, 'page3': page3})

        t = template.Template('{% load feincms_page_tags %}{% feincms_parentlink of feincms_page level=1 %}')
        self.assertEqual(t.render(context), '/test-page/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_languagelinks for feincms_page as links %}{% for key, name, link in links %}{{ key }}:{{ link }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), 'en:/test-page/,de:/test-page/test-child-page/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_languagelinks for page3 as links %}{% for key, name, link in links %}{{ key }}:{{ link }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), 'en:/test-page/test-child-page/page3/,de:None')

        t = template.Template('{% load feincms_page_tags %}{% feincms_languagelinks for page3 as links existing %}{% for key, name, link in links %}{{ key }}:{{ link }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), 'en:/test-page/test-child-page/page3/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_languagelinks for feincms_page as links excludecurrent=1 %}{% for key, name, link in links %}{{ key }}:{{ link }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), 'en:/test-page/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=1 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), '')

        # XXX should the other template tags not respect the in_navigation setting too?
        page1.active = True
        page1.in_navigation = True
        page1.save()

        self.assertEqual(t.render(context), '/test-page/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), '/test-page/test-child-page/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of request as nav level=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        from django.http import HttpRequest
        request = HttpRequest()
        request.path = '/test-page/'
        self.assertEqual(t.render(template.Context({'request': request})), '/test-page/test-child-page/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=99 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), '')

        t = template.Template('{% load feincms_page_tags %}{% feincms_breadcrumbs feincms_page %}')
        rendered = t.render(context)
        self.assertTrue("Test child page" in rendered)
        self.assertTrue('href="/test-page/">Test page</a>' in rendered, msg="The parent page should be a breadcrumb link")
        self.assertTrue('href="/test-page/test-child-page/"' not in rendered, msg="The current page should not be a link in the breadcrumbs")

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=2,depth=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), '/test-page/test-child-page/,/test-page/test-child-page/page3/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=1,depth=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), '/test-page/,/test-page/test-child-page/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=1,depth=3 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), '/test-page/,/test-page/test-child-page/,/test-page/test-child-page/page3/')

        t = template.Template('{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=3,depth=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}')
        self.assertEqual(t.render(context), '/test-page/test-child-page/page3/')

        t = template.Template('{% load feincms_page_tags %}{% if feincms_page|is_parent_of:page3 %}yes{% endif %}|{% if page3|is_parent_of:feincms_page %}yes{% endif %}')
        self.assertEqual(t.render(context), 'yes|')

        t = template.Template('{% load feincms_page_tags %}{% if feincms_page|is_equal_or_parent_of:page3 %}yes{% endif %}|{% if page3|is_equal_or_parent_of:feincms_page %}yes{% endif %}')
        self.assertEqual(t.render(context), 'yes|')

        t = template.Template('{% load feincms_page_tags %}{% feincms_translatedpage for feincms_page as t1 language=de %}{% feincms_translatedpage for feincms_page as t2 %}{{ t1.id }}|{{ t2.id }}')
        self.assertEqual(t.render(context), '2|1')

    def test_17_feincms_navigation(self):
        """
        Test feincms_navigation some more
        """

        self.login()

        self.create_page('Page 1')
        self.create_page('Page 1.1', 1)
        self.create_page('Page 1.2', 1)
        self.create_page('Page 1.2.1', 3)
        self.create_page('Page 1.2.2', 3)
        self.create_page('Page 1.2.3', 3)
        self.create_page('Page 1.3', 1)

        self.create_page('Page 2')
        self.create_page('Page 2.1', 8)
        self.create_page('Page 2.2', 8)
        self.create_page('Page 2.3', 8)

        self.create_page('Page 3')
        self.create_page('Page 3.1', 12)
        self.create_page('Page 3.2', 12)
        self.create_page('Page 3.3', 12)
        self.create_page('Page 3.3.1', 15)
        self.create_page('Page 3.3.1.1', 16)
        self.create_page('Page 3.3.2', 15)

        self.create_page('Page 4')
        self.create_page('Page 4.1', 19)
        self.create_page('Page 4.2', 19)

        Page.objects.all().update(active=True, in_navigation=True)
        Page.objects.filter(id__in=(5, 9, 19)).update(in_navigation=False)

        tests = [
            (
                {'feincms_page': Page.objects.get(pk=1)},
                '{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=1,depth=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}',
                '/page-1/,/page-1/page-11/,/page-1/page-12/,/page-1/page-13/,/page-2/,/page-2/page-22/,/page-2/page-23/,/page-3/,/page-3/page-31/,/page-3/page-32/,/page-3/page-33/',
            ),
            (
                {'feincms_page': Page.objects.get(pk=14)},
                '{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=2,depth=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}',
                '/page-3/page-31/,/page-3/page-32/,/page-3/page-33/,/page-3/page-33/page-331/,/page-3/page-33/page-332/',
            ),
            (
                {'feincms_page': Page.objects.get(pk=14)},
                '{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=2,depth=3 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}',
                '/page-3/page-31/,/page-3/page-32/,/page-3/page-33/,/page-3/page-33/page-331/,/page-3/page-33/page-331/page-3311/,/page-3/page-33/page-332/',
            ),
            (
                {'feincms_page': Page.objects.get(pk=19)},
                '{% load feincms_page_tags %}{% feincms_navigation of feincms_page as nav level=1,depth=2 %}{% for p in nav %}{{ p.get_absolute_url }}{% if not forloop.last %},{% endif %}{% endfor %}',
                '/page-1/,/page-1/page-11/,/page-1/page-12/,/page-1/page-13/,/page-2/,/page-2/page-22/,/page-2/page-23/,/page-3/,/page-3/page-31/,/page-3/page-32/,/page-3/page-33/',
            ),
        ]

        for c, t, r in tests:
            self.assertEqual(
                template.Template(t).render(template.Context(c)),
                r)

    def test_18_default_render_method(self):
        """
        Test the default render() behavior of selecting render_<region> methods
        to do the (not so) heavy lifting.
        """

        class Something(models.Model):
            class Meta:
                abstract = True

            def render_main(self):
                return u'Hello'

        # do not register this model in the internal FeinCMS bookkeeping structures
        tmp = Page._feincms_content_types[:]
        type = Page.create_content_type(Something, regions=('notexists',))
        Page._feincms_content_types = tmp

        s = type(region='main', ordering='1')

        self.assertEqual(s.render(), 'Hello')

    def test_19_page_manager(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=2)
        page.active = True
        page.save()

        self.assertEqual(page, Page.objects.page_for_path(page.get_absolute_url()))
        self.assertEqual(page, Page.objects.best_match_for_path(page.get_absolute_url() + 'something/hello/'))

        self.assertRaises(Http404, lambda: Page.objects.best_match_for_path('/blabla/blabla/', raise404=True))
        self.assertRaises(Http404, lambda: Page.objects.page_for_path('/asdf/', raise404=True))
        self.assertRaises(Page.DoesNotExist, lambda: Page.objects.best_match_for_path('/blabla/blabla/'))
        self.assertRaises(Page.DoesNotExist, lambda: Page.objects.page_for_path('/asdf/'))

        request = Empty()
        request.path = page.get_absolute_url()
        request.method = 'GET'
        request.get_full_path = lambda: '/xyz/'
        request.GET = {}
        request.META = {}
        request.user = AnonymousUser()

        # tadaa
        from django.utils import translation
        translation.activate(page.language)

        page.active = False
        page.save()

        self.assertRaises(Http404, lambda: Page.objects.for_request(request, raise404=True))

        page.active = True
        page.save()

        self.assertRaises(Http404, lambda: Page.objects.for_request(request, raise404=True))

        page.parent.active = True
        page.parent.save()
        self.assertEqual(page, Page.objects.for_request(request))

        old = feincms_settings.FEINCMS_ALLOW_EXTRA_PATH
        request.path += 'hello/'

        feincms_settings.FEINCMS_ALLOW_EXTRA_PATH = False
        self.assertEqual(self.client.get(request.path).status_code, 404)

        feincms_settings.FEINCMS_ALLOW_EXTRA_PATH = True
        self.assertEqual(self.client.get(request.path).status_code, 200)
        self.assertEqual(page, Page.objects.for_request(request, best_match=True))

        feincms_settings.FEINCMS_ALLOW_EXTRA_PATH = old

        page_id = id(request._feincms_page)
        p = Page.objects.for_request(request)
        self.assertEqual(id(p), page_id)

    def test_20_redirects(self):
        self.create_default_page_set()
        page1 = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)

        page2.active = True
        page2.publication_date = datetime.now() - timedelta(days=1)
        page2.override_url = '/blablabla/'
        page2.redirect_to = page1.get_absolute_url()
        page2.save()

        # regenerate cached URLs in the whole tree
        page1.active = True
        page1.save()

        page2 = Page.objects.get(pk=2)

        # page2 has been modified too, but its URL should not have changed
        try:
            self.assertRedirects(self.client.get('/blablabla/'), page1.get_absolute_url())
        except TemplateDoesNotExist, e:
            # catch the error from rendering page1
            if e.args != ('feincms_base.html',):
                raise

    def test_21_copy_content(self):
        self.create_default_page_set()
        page = Page.objects.get(pk=1)
        self.create_pagecontent(page)

        page2 = Page.objects.get(pk=2)
        page2.copy_content_from(page)
        self.assertEqual(len(page2.content.main), 1)

    def test_22_contactform(self):
        self.create_default_page_set()
        page = Page.objects.get(pk=1)
        page.active = True
        page.template_key = 'theother'
        page.save()

        page.contactformcontent_set.create(email='mail@example.com', subject='bla',
                                           region='main', ordering=0)

        request = Empty()
        request.method = 'GET'
        request.GET = {}
        request.META = {}
        request.user = Empty()
        request.user.is_authenticated = lambda: False
        request.user.get_and_delete_messages = lambda: ()

        page.content.main[0].process(request)
        self.assertTrue('form' in page.content.main[0].render(request=request))

        self.client.post(page.get_absolute_url(), {
            'name': 'So what\'s your name, dude?',
            'email': 'another@example.com',
            'subject': 'This is a test. Please calm down',
            'content': 'Hell on earth.',
            })

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, 'This is a test. Please calm down')

    def test_23_navigation_extension(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)

        self.assertEqual(len(page.extended_navigation()), 0)

        page.navigation_extension = 'feincms.tests.navigation_extensions.PassthroughExtension'

        page2 = Page.objects.get(pk=2)
        page2.active = True
        page2.in_navigation = True
        page2.save()

        self.assertEqual(list(page.extended_navigation()), [page2])

        page.navigation_extension = 'feincms.tests.navigation_extensions.ThisExtensionDoesNotExist'

        self.assertEqual(len(page.extended_navigation()), 1)

        page.navigation_extension = 'feincms.tests.navigation_extensions.PretenderExtension'

        self.assertEqual(page.extended_navigation()[0].get_absolute_url(), '/asdsa/')

    def test_24_admin_redirects(self):
        self.create_default_page_set()
        page = Page.objects.get(pk=1)

        response = self.create_pagecontent(page, _continue=1)
        self.assertRedirects(response, '/admin/page/page/1/')

        response = self.create_pagecontent(page, _addanother=1)
        self.assertRedirects(response, '/admin/page/page/add/')

        response = self.create_pagecontent(page)
        self.assertRedirects(response, '/admin/page/page/')

    def test_25_applicationcontent(self):
        self.create_default_page_set()

        page1 = Page.objects.get(pk=1)
        page1.active = True
        page1.save()

        page = Page.objects.get(pk=2)
        page.active = True
        page.template_key = 'theother'
        page.save()

        # Should not be published because the page has no application contents and should
        # therefore not catch anything below it.
        self.is_published(page1.get_absolute_url() + 'anything/', False)

        page.applicationcontent_set.create(
            region='main', ordering=0,
            urlconf_path='feincms.tests.applicationcontent_urls')

        self.assertContains(self.client.get(page.get_absolute_url()),
                            'module_root')
        self.assertContains(self.client.get(page.get_absolute_url() + 'args_test/abc/def/'),
                            'abc-def')
        self.assertContains(self.client.get(page.get_absolute_url() + 'kwargs_test/abc/def/'),
                            'def-abc')

        response = self.client.get(page.get_absolute_url() + 'reverse_test/')
        self.assertContains(response, 'home:/test-page/test-child-page/')
        self.assertContains(response, 'args:/test-page/test-child-page/args_test/xy/zzy/')
        self.assertContains(response, 'base:/test/')

        response = self.client.get(page.get_absolute_url() + 'full_reverse_test/')
        self.assertContains(response, 'home:/test-page/test-child-page/')
        self.assertContains(response, 'args:/test-page/test-child-page/args_test/xy/zzy/')
        self.assertContains(response, 'base:/test/')

        self.assertEqual(reverse('feincms.tests.applicationcontent_urls/ac_module_root'),
            '/test-page/test-child-page/')

        if hasattr(self, 'assertNumQueries'):
            self.assertNumQueries(0,
                lambda: reverse('feincms.tests.applicationcontent_urls/ac_module_root'))

            _empty_reverse_cache()

            self.assertNumQueries(1,
                lambda: reverse('feincms.tests.applicationcontent_urls/ac_module_root'))
            self.assertNumQueries(0,
                lambda: reverse('feincms.tests.applicationcontent_urls/ac_module_root'))

        # This should not raise
        self.assertEquals(self.client.get(page.get_absolute_url() + 'notexists/').status_code, 404)

        self.assertContains(self.client.get(page.get_absolute_url() + 'fragment/'),
                            '<span id="something">some things</span>')

        self.assertRedirects(self.client.get(page.get_absolute_url() + 'redirect/'),
                             page.get_absolute_url())

        self.assertEqual(reverse('feincms.tests.applicationcontent_urls/ac_module_root'),
            page.get_absolute_url())

        response = self.client.get(page.get_absolute_url() + 'response/')
        self.assertContains(response, 'Anything')
        self.assertContains(response, '<h2>Main content</h2>') # Ensure response has been wrapped

        # Test standalone behavior
        self.assertEqual(
            self.client.get(page.get_absolute_url() + 'response/',
                HTTP_X_REQUESTED_WITH='XMLHttpRequest').content,
            self.client.get(page.get_absolute_url() + 'response_decorated/').content)

        # Test reversing of URLs (with overridden urls too)
        page.applicationcontent_set.create(
            region='main',
            ordering=1,
            urlconf_path='blog_urls')
        page1.applicationcontent_set.create(
            region='main',
            ordering=0,
            urlconf_path='whatever')

        response = self.client.get(page.get_absolute_url() + 'alias_reverse_test/')
        self.assertContains(response, 'home:/test-page/')
        self.assertContains(response, 'args:/test-page/args_test/xy/zzy/')
        self.assertContains(response, 'base:/test/')

        self.assertEqual(reverse('blog_urls/blog_entry_list'), '/test-page/test-child-page/')
        self.assertEqual(reverse('feincms.tests.applicationcontent_urls/ac_module_root'),
            '/test-page/test-child-page/')
        self.assertEqual(reverse('whatever/ac_module_root'), '/test-page/')

        page.applicationcontent_set.get(urlconf_path='feincms.tests.applicationcontent_urls').delete()

        self.assertEqual(reverse('blog_urls/blog_entry_list'), '/test-page/test-child-page/')
        self.assertEqual(reverse('whatever/ac_module_root'), '/test-page/')

    def test_26_page_form_initial(self):
        self.create_default_page_set()

        self.assertEqual(self.client.get('/admin/page/page/add/?translation_of=1&lang=de').status_code, 200)
        self.assertEqual(self.client.get('/admin/page/page/add/?parent=1').status_code, 200)
        self.assertEqual(self.client.get('/admin/page/page/add/?parent=2').status_code, 200)

    def test_27_cached_url_clash(self):
        self.create_default_page_set()

        page1 = Page.objects.get(pk=1)
        page2 = Page.objects.get(pk=2)

        page1.override_url = '/'
        page1.active = True
        page1.save()

        self.assertContains(self.create_pagecontent(page2, active=True, override_url='/'),
            'already taken by')

    def test_28_applicationcontent_reverse(self):
        self.create_default_page_set()
        page1 = Page.objects.get(pk=1)
        page1.active = True
        page1.save()

        page = Page.objects.get(pk=2)
        page.active = True
        page.template_key = 'theother'
        page.save()
        page.applicationcontent_set.create(
            region='main', ordering=0,
            urlconf_path='feincms.tests.applicationcontent_urls')

        from django.core.urlresolvers import reverse

        # test reverse replacement
        self.assertEqual(reverse('feincms.tests.applicationcontent_urls/ac_module_root'),
                         page.get_absolute_url())


        # when specific applicationcontent exists more then once reverse should return url
        # for the one that has tree_id same as current feincms page
        self.create_page(title='Home DE', language='de', active=True)
        page_de = Page.objects.get(title='Home DE')
        self.create_page(title='Child 1 DE', language='de', parent=page_de.id, active=True)
        page_de_1 = Page.objects.get(title='Child 1 DE')
        page_de_1.applicationcontent_set.create(
            region='main', ordering=0,
            urlconf_path='feincms.tests.applicationcontent_urls')
        _empty_reverse_cache()

        settings.TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)
        self.client.get(page_de.get_absolute_url())
        self.assertEqual(reverse('feincms.tests.applicationcontent_urls/ac_module_root'),
                         page_de_1.get_absolute_url())

        self.client.get(page1.get_absolute_url())
        self.assertEqual(reverse('feincms.tests.applicationcontent_urls/ac_module_root'),
                      page.get_absolute_url())

    def test_29_medialibrary_admin(self):
        self.create_default_page_set()

        page = Page.objects.get(pk=1)

        path = os.path.join(settings.MEDIA_ROOT, 'somefile.jpg')
        f = open(path, 'wb')
        f.write('blabla')
        f.close()

        mediafile = MediaFile.objects.create(file='somefile.jpg')
        page.mediafilecontent_set.create(
            mediafile=mediafile,
            region='main',
            position='block',
            ordering=1)

        self.assertContains(self.client.get('/admin/medialibrary/mediafile/'), 'somefile.jpg')

        import zipfile
        zf = zipfile.ZipFile('test.zip', 'w')
        for i in range(10):
            zf.writestr('test%d.jpg' % i, 'test%d' % i)
        zf.close()

        self.assertRedirects(self.client.post('/admin/medialibrary/mediafile/mediafile-bulk-upload/', {
            'data': open('test.zip'),
            }), '/admin/medialibrary/mediafile/')

        self.assertEqual(MediaFile.objects.count(), 11)

        self.assertRedirects(self.client.post('/admin/medialibrary/mediafile/add/', {
            'file': open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'docs', 'images', 'tree_editor.png')),
            'translations-TOTAL_FORMS': 0,
            'translations-INITIAL_FORMS': 0,
            'translations-MAX_NUM_FORMS': 10,
            }), '/admin/medialibrary/mediafile/')

        self.assertContains(self.client.get('/admin/medialibrary/mediafile/'),
            '100x100.png" alt="" />')

        stats = list(MediaFile.objects.values_list('type', flat=True))
        self.assertEqual(stats.count('image'), 1)
        self.assertEqual(stats.count('other'), 11)

    def test_30_context_processors(self):
        self.create_default_page_set()
        Page.objects.update(active=True, in_navigation=True)

        request = Empty()
        request.GET = {}
        request.META = {}
        request.method = 'GET'
        request.path = '/test-page/test-child-page/abcdef/'
        request.get_full_path = lambda: '/test-page/test-child-page/abcdef/'

        ctx = add_page_if_missing(request)
        self.assertEqual(ctx['feincms_page'], request._feincms_page)

    def test_31_sites_framework_associating_with_single_site(self):
        self.login()
        site_2 = Site.objects.create(name='site 2', domain='2.example.com')
        self.create_page('site 1 homepage', override_url='/', active=True)
        self.create_page('site 2 homepage', override_url='/',
                site=site_2.id, active=True)
        self.assertEqual(Page.objects.count(), 2)
        self.assertEqual(Page.objects.active().count(), 1)


Entry.register_extensions('seo', 'translations', 'seo', 'ct_tracker')
class BlogTestCase(TestCase):
    def setUp(self):
        u = User(username='test', is_active=True, is_staff=True, is_superuser=True)
        u.set_password('test')
        u.save()

        Entry.register_regions(('main', 'Main region'), ('another', 'Another region'))
        Entry.prefilled_categories = prefilled_attribute('categories')
        Entry.prefilled_rawcontent_set = prefilled_attribute('rawcontent_set')

    def login(self):
        self.assertTrue(self.client.login(username='test', password='test'))

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

        return entry

    def create_entries(self):
        entry = self.create_entry()

        Entry.objects.create(
            published=True,
            title='Something 2',
            slug='something-2',
            language='de',
            translation_of=entry)

        Entry.objects.create(
            published=True,
            title='Something 3',
            slug='something-3',
            language='de')

    def test_01_prefilled_attributes(self):
        self.create_entry()

        # This should return silently
        objects = prefill_entry_list(Entry.objects.none(), 'rawcontent_set', 'categories')

        objects = prefill_entry_list(Entry.objects.published(), 'rawcontent_set', 'categories')

        self.assertEqual(len(objects[0]._prefill_categories), 0)
        self.assertEqual(len(objects[0]._prefill_rawcontent_set), 1)
        self.assertEqual(unicode(objects[0]), 'Something')

        objects = Entry.objects.published()

        self.assertEqual(len(objects[0].prefilled_categories), 0)
        self.assertEqual(len(objects[0].prefilled_rawcontent_set), 1)

        objects = prefill_entry_list(Entry.objects.published(), 'rawcontent_set', 'categories', region='another')

        self.assertEqual(len(objects[0]._prefill_categories), 0)
        self.assertEqual(len(objects[0]._prefill_rawcontent_set), 0)

        self.login()
        self.assertEqual(self.client.get('/admin/blog/entry/').status_code, 200)
        self.assertEqual(self.client.get('/admin/blog/entry/1/').status_code, 200)

    def test_02_translations(self):
        self.create_entries()

        entries = Entry.objects.in_bulk((1, 2, 3))

        self.assertEqual(len(entries[1].available_translations()), 1)
        self.assertEqual(len(entries[2].available_translations()), 1)
        self.assertEqual(len(entries[3].available_translations()), 0)

    def test_03_admin(self):
        self.login()
        self.create_entries()
        self.assertEqual(self.client.get('/admin/blog/entry/').status_code, 200)
        self.assertEqual(self.client.get('/admin/blog/entry/1/').status_code, 200)


class CleanseTestCase(TestCase):
    def test_01_cleanse(self):
        from feincms.utils.html.cleanse import cleanse_html

        entries = [
            (u'<p>&nbsp;</p>', u''),
            (u'<span style="font-weight: bold;">Something</span><p></p>', u'<strong>Something</strong>'),
            (u'<p>abc <span>def <em>ghi</em> jkl</span> mno</p>', u'<p>abc def <em>ghi</em> jkl mno</p>'),
            (u'<span style="font-style: italic;">Something</span><p></p>', u'<em>Something</em>'),
            (u'<p>abc<br />def</p>', u'<p>abc<br />def</p>'),
            (u'<p><p><p>&nbsp;</p> </p><p><br /></p></p>', u' '),
            ]

        for a, b in entries:
            self.assertEqual(cleanse_html(a), b)
