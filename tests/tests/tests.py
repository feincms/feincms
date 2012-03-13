# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from datetime import datetime, timedelta
import os
import re

from django import forms, template
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.sites.models import Site
from django.http import Http404, HttpResponseBadRequest
from django.template import TemplateDoesNotExist
from django.template.defaultfilters import slugify
from django.test import TestCase

from feincms import settings as feincms_settings
from feincms.content.application.models import _empty_reverse_cache
from feincms.content.contactform.models import ContactFormContent, ContactForm
from feincms.content.file.models import FileContent
from feincms.content.image.models import ImageContent
from feincms.content.raw.models import RawContent
from feincms.content.richtext.models import RichTextContent

from feincms.context_processors import add_page_if_missing
from feincms.models import Region, Template, Base, ContentProxy
from feincms.module.blog.models import Entry
from feincms.module.medialibrary.models import Category, MediaFile
from feincms.module.page import processors
from feincms.module.page.models import Page
from feincms.templatetags import feincms_tags
from feincms.translations import short_language_code
from feincms.utils import collect_dict_values, get_object

# ------------------------------------------------------------------------
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

Page.register_extensions('datepublisher', 'navigation', 'seo', 'symlinks',
                         'titles', 'translations', 'seo', 'changedate',
                         'ct_tracker')
Page.create_content_type(ContactFormContent, form=ContactForm)
Page.create_content_type(FileContent)
Page.register_request_processor(processors.etag_request_processor)
Page.register_response_processor(processors.etag_response_processor)
Page.register_response_processor(processors.debug_sql_queries_response_processor())


Entry.register_extensions('seo', 'translations', 'seo', 'ct_tracker')
class BlogTestCase(TestCase):
    def setUp(self):
        u = User(username='test', is_active=True, is_staff=True, is_superuser=True)
        u.set_password('test')
        u.save()

        Entry.register_regions(('main', 'Main region'), ('another', 'Another region'))

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
