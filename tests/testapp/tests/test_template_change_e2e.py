"""
End-to-end test for Issue #677 (Double Submission on Template Change) using Playwright.

This test verifies that the JavaScript fix actually works in a real browser environment
by checking that submit buttons are disabled after a template change is triggered.
"""

import os

import pytest
from django.contrib.auth.models import User
from playwright.sync_api import expect

from feincms.module.page.models import Page


# Set Django async unsafe to allow database operations in tests
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.mark.django_db
@pytest.mark.e2e
def test_double_submission_protection(page, live_server):
    """
    Test that submit buttons are disabled after template change.

    This verifies the fix for Issue #677 by:
    1. Logging into the admin
    2. Navigating to a Page change view
    3. Changing the template to trigger the on_template_key_changed event
    4. Accepting the confirmation alert
    5. Verifying that the Save button is immediately disabled
    """
    # Register templates
    Page._feincms_templates = {}
    Page.register_templates(
        {
            "key": "base",
            "title": "Base Template",
            "path": "feincms_base.html",
            "regions": (
                ("main", "Main content area"),
                ("sidebar", "Sidebar", "inherited"),
            ),
        },
        {
            "key": "theother",
            "title": "Alternative Template",
            "path": "base.html",
            "regions": (
                ("main", "Main content area"),
                ("sidebar", "Sidebar", "inherited"),
            ),
        },
    )

    # Create superuser
    username = "admin"
    password = "testpass123"
    User.objects.create_superuser(
        username=username, email="admin@test.com", password=password
    )

    # Create a test Page with initial template_key='base'
    test_page = Page.objects.create(
        title="Test Page",
        slug="test-page",
        template_key="base",
        active=True,
        in_navigation=True,
    )

    # Log in to Django admin
    page.goto(f"{live_server.url}/admin/login/")
    page.fill("#id_username", username)
    page.fill("#id_password", password)
    page.click('input[type="submit"]')

    # Navigate to the Page change view
    page.goto(f"{live_server.url}/admin/page/page/{test_page.pk}/change/")

    # Wait for the page to load - check specifically for the form
    page.wait_for_load_state("networkidle")
    page.wait_for_selector('form[method="post"]')

    # Verify jQuery and JavaScript are loaded
    jquery_loaded = page.evaluate("typeof jQuery !== 'undefined'")
    template_regions_loaded = page.evaluate("typeof template_regions !== 'undefined'")

    if not jquery_loaded or not template_regions_loaded:
        pytest.skip(
            f"JavaScript not properly loaded (jQuery: {jquery_loaded}, "
            f"template_regions: {template_regions_loaded}). This test requires full admin static files."
        )

    # Find the template key input - could be either select or radio buttons
    template_inputs = page.locator('input[name="template_key"]').count()

    # Set up dialog handler BEFORE changing the template
    dialog_accepted = []

    def handle_dialog(dialog):
        dialog.accept()
        dialog_accepted.append(True)

    page.on("dialog", handle_dialog)

    if template_inputs == 0:
        # It's a select dropdown
        select = page.locator('select[name="template_key"]')
        current_value = select.input_value()
        # Change to a different template
        options = select.locator("option").all()
        for option in options:
            value = option.get_attribute("value")
            if value and value != current_value:
                select.select_option(value)
                break
    else:
        # It's radio buttons - use JavaScript to trigger the change since inputs are hidden
        radios = page.locator('input[name="template_key"]').all()
        for i, radio in enumerate(radios):
            if not radio.is_checked():
                # Use JavaScript to check the radio and trigger the change event
                radio.evaluate("el => { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); el.click(); }")
                break

    # Wait for the dialog to be handled
    page.wait_for_timeout(500)

    # Verify that the dialog was shown and accepted
    assert len(dialog_accepted) > 0, "Expected confirmation dialog did not appear"

    # CRITICAL ASSERTION: Verify that the Save button is disabled
    # This should happen immediately after accepting the dialog
    # Give a bit of time for the JavaScript to disable the button
    page.wait_for_timeout(100)
    save_button = page.locator('input[name="_save"]')

    # Check if the button is disabled (it should be to prevent double submission)
    expect(save_button).to_be_disabled(timeout=1000)
