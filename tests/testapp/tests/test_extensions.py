# coding: utf-8
from __future__ import absolute_import

from django.template.defaultfilters import slugify
from django.test.utils import override_settings
from django.test import TestCase
from django.contrib.sites.models import Site

from feincms.module.page.models import Page


from .utils import reset_page_db



class TranslationTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        Page.register_extensions('feincms.module.extensions.translations',)
        reset_page_db()

    def setUp(self):
        Page.register_templates({
            'key': 'base',
            'title': 'Standard template',
            'path': 'feincms_base.html',
            'regions': (
                ('main', 'Main content area'),
                ('sidebar', 'Sidebar', 'inherited'),
            ),
        })
        self.site_1 = Site.objects.all()[0]

        # create a bunch of pages
        en = self.create_default_page_set(language='en')
        de = self.create_default_page_set(language='de', title=u'Testseite')
        de.translation_of = en
        de.save()
        de.parent.translation_of = en.parent
        de.parent.save()
        self.page_de = de.parent
        self.page_en = en.parent


    def create_page(self, title='Test page', parent=None, **kwargs):
        defaults = {
            'template_key': 'base',
            'site': self.site_1,
            'in_navigation': False,
            'active': False,
            }
        defaults.update(kwargs)
        return Page.objects.create(
            title=title,
            slug=kwargs.get('slug', slugify(title)),
            parent=parent,
            **defaults)

    def create_default_page_set(self, **kwargs):
        return self.create_page(
            'Test child page',
            parent=self.create_page(**kwargs),
        )

    def testPage(self):
        page = Page()
        self.assertTrue(hasattr(page, 'language'))
        self.assertTrue(hasattr(page, 'translation_of'))
        self.assertEqual(self.page_de.translation_of, self.page_en)
        self.assertEqual(self.page_de.original_translation, self.page_en)

        # TODO:  add request tests
        # with translation.override('de'):