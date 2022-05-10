
from unittest import skipIf

from django import VERSION
from django.conf import settings as django_settings
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify
from django.test import RequestFactory, TestCase
from django.utils import translation

from feincms.extensions.translations import (
    translation_set_language,
    user_has_language_set,
)
from feincms.module.page.models import Page


class TranslationTestCase(TestCase):
    def setUp(self):
        Page.register_templates(
            {
                "key": "base",
                "title": "Standard template",
                "path": "feincms_base.html",
                "regions": (
                    ("main", "Main content area"),
                    ("sidebar", "Sidebar", "inherited"),
                ),
            }
        )
        self.site_1 = Site.objects.all()[0]

        # create a bunch of pages
        en = self.create_default_page_set(language="en")
        de = self.create_default_page_set(language="de", title="Testseite")
        de.translation_of = en
        de.save()
        de.parent.translation_of = en.parent
        de.parent.save()
        self.page_de = de.parent
        self.page_en = en.parent

        if hasattr(translation, "LANGUAGE_SESSION_KEY"):
            self.language_session_key = translation.LANGUAGE_SESSION_KEY
        else:
            # Django 1.6
            self.language_session_key = django_settings.LANGUAGE_COOKIE_NAME

    def create_page(self, title="Test page", parent=None, **kwargs):
        defaults = {
            "template_key": "base",
            "site": self.site_1,
            "in_navigation": False,
            "active": False,
        }
        defaults.update(kwargs)
        return Page.objects.create(
            title=title,
            slug=kwargs.get("slug", slugify(title)),
            parent=parent,
            **defaults
        )

    def create_default_page_set(self, **kwargs):
        return self.create_page("Test child page", parent=self.create_page(**kwargs))

    def testPage(self):
        page = Page()
        self.assertTrue(hasattr(page, "language"))
        self.assertTrue(hasattr(page, "translation_of"))
        self.assertEqual(self.page_de.translation_of, self.page_en)
        self.assertEqual(self.page_de.original_translation, self.page_en)

        # TODO:  add request tests
        # with translation.override('de'):

    def test_user_has_language_set_with_session(self):
        factory = RequestFactory()
        request = factory.get(self.page_en.get_navigation_url())
        setattr(request, "session", dict())
        request.session[self.language_session_key] = "en"
        self.assertEqual(user_has_language_set(request), True)

    def test_user_has_language_set_with_cookie(self):
        factory = RequestFactory()
        request = factory.get(self.page_en.get_navigation_url())
        request.COOKIES[django_settings.LANGUAGE_COOKIE_NAME] = "en"

        self.assertEqual(user_has_language_set(request), True)

    def test_translation_set_language_to_session(self):
        factory = RequestFactory()
        request = factory.get(self.page_de.get_navigation_url())
        setattr(request, "session", dict())
        translation_set_language(request, "de")

        self.assertEqual(request.LANGUAGE_CODE, "de")
        self.assertEqual(request.session[self.language_session_key], "de")

    def test_translation_set_language_to_session_primary(self):
        factory = RequestFactory()
        request = factory.get(self.page_en.get_navigation_url())
        setattr(request, "session", dict())
        translation_set_language(request, "en")

        self.assertEqual(request.LANGUAGE_CODE, "en")
        # We avoid setting the translation language to the primary language, so should not be set
        self.assertEqual(request.session.get(self.language_session_key, 'unset'), "unset")

    def test_translation_set_language_to_cookie(self):
        factory = RequestFactory()
        request = factory.get(self.page_en.get_navigation_url())
        response = translation_set_language(request, "en")

        self.assertEqual(request.LANGUAGE_CODE, "en")

        c_key = django_settings.LANGUAGE_COOKIE_NAME
        self.assertEqual(response.cookies[c_key].value, "en")
