# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import doctest

from django.contrib.auth.models import User
from django.test import TestCase

import feincms

from feincms.content.contactform.models import ContactFormContent, ContactForm
from feincms.content.file.models import FileContent

from feincms.models import Region, Template, Base
from feincms.module.blog.models import Entry
from feincms.module.page import processors
from feincms.module.page.models import Page
from feincms.utils import collect_dict_values, get_object

# ------------------------------------------------------------------------
class Empty(object):
    """
    Helper class to use as request substitute (or whatever)
    """

    pass

class DocTest(TestCase):
    def test_translation_short_language_code(self):
        doctest.testmod(feincms.translations)

    def test_medialibrary_doctests(self):
        doctest.testmod(feincms.module.medialibrary.models)

    def test_utils(self):
        doctest.testmod(feincms.utils)

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

Page.register_extensions(
    'feincms.module.extensions.datepublisher',
    'feincms.module.extensions.translations',
    'feincms.module.extensions.ct_tracker',
    'feincms.module.extensions.seo',
    'feincms.module.extensions.changedate',
    'feincms.module.extensions.seo',  # duplicate
    'feincms.module.page.extensions.navigation',
    'feincms.module.page.extensions.symlinks',
    'feincms.module.page.extensions.titles',
    )
Page.create_content_type(ContactFormContent, form=ContactForm)
Page.create_content_type(FileContent)
Page.register_request_processor(processors.etag_request_processor)
Page.register_response_processor(processors.etag_response_processor)
Page.register_response_processor(processors.debug_sql_queries_response_processor())


class BlogTestCase(TestCase):
    def setUp(self):
        u = User(username='test', is_active=True, is_staff=True, is_superuser=True)
        u.set_password('test')
        u.save()

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

    def test_01_smoke_test_admin(self):
        self.create_entry()

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
