"""
End-to-end test for Issue #400: Many-to-many selections using
``filter_horizontal`` must survive changing the page template.

Run with: tox -e e2e
"""

import os


try:
    import pytest

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    pytest = None

from django.contrib.auth.models import User

from feincms.module.page.models import Page
from testapp.content import CategoriesContent
from testapp.models import Category


os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


if PLAYWRIGHT_AVAILABLE:

    @pytest.mark.django_db
    @pytest.mark.e2e
    def test_m2m_selection_survives_template_change(page, live_server):
        Page._feincms_templates = {}
        Page.register_templates(
            {
                "key": "base",
                "title": "Base Template",
                "path": "feincms_base.html",
                "regions": (("main", "Main content area"),),
            },
            {
                "key": "theother",
                "title": "Alternative Template",
                "path": "base.html",
                "regions": (("main", "Main content area"),),
            },
        )

        User.objects.create_superuser("admin", "admin@test.com", "testpass123")

        test_page = Page.objects.create(
            title="Test Page", slug="test-page", template_key="base"
        )
        content = Page.content_type_for(CategoriesContent).objects.create(
            parent=test_page, region="main", ordering=0
        )
        categories = [
            Category.objects.create(name=name, slug=name) for name in ("one", "two")
        ]
        content.categories.set(categories)

        page.goto(f"{live_server.url}/admin/login/")
        page.fill("#id_username", "admin")
        page.fill("#id_password", "testpass123")
        page.click('input[type="submit"]')

        page.goto(f"{live_server.url}/admin/page/page/{test_page.pk}/change/")
        page.wait_for_load_state("networkidle")

        # The item editor and the filter_horizontal widget have to be active,
        # otherwise this test doesn't test anything.
        assert page.evaluate("typeof template_regions") == "object"
        assert page.locator(".selector-chosen select option").count() == 2

        page.on("dialog", lambda dialog: dialog.accept())
        with page.expect_navigation():
            radio = page.locator('input[name="template_key"][value="theother"]')
            if radio.count():
                radio.evaluate("el => el.click()")
            else:
                page.select_option('select[name="template_key"]', "theother")
        page.wait_for_load_state("networkidle")

        assert page.locator(".errornote").count() == 0, page.content()
        test_page.refresh_from_db()
        assert test_page.template_key == "theother"
        content.refresh_from_db()
        assert set(content.categories.all()) == set(categories)
