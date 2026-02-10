"""
Selenium-based behavioral test for Issue #677 (Double Submission on Template Change).

This test verifies that the JavaScript fix actually works in a real browser environment
by checking that submit buttons are disabled after a template change is triggered.

NOTE: This test requires selenium and Chrome/ChromeDriver to be installed.
If not available, the test will be skipped.
"""

import unittest
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from feincms.module.page.models import Page


@unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium not installed")
class TemplateChangeSeleniumTest(StaticLiveServerTestCase):
    """Test that the double submission fix works in a real browser environment."""

    @classmethod
    def setUpClass(cls):
        """Initialize the headless Chrome WebDriver."""
        super().setUpClass()

        # Configure Chrome options for headless mode
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        try:
            cls.selenium = webdriver.Chrome(options=chrome_options)
            cls.selenium.implicitly_wait(10)
        except Exception as e:
            raise Exception(
                f"Failed to initialize Chrome WebDriver. "
                f"Please ensure Chrome/Chromium and ChromeDriver are installed. "
                f"Error: {e}"
            )

    @classmethod
    def tearDownClass(cls):
        """Quit the WebDriver."""
        if hasattr(cls, "selenium"):
            cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        """Create test data: superuser and test Page."""
        # Create superuser
        self.username = "admin"
        self.password = "testpass123"
        self.user = User.objects.create_superuser(
            username=self.username, email="admin@test.com", password=self.password
        )

        # Register templates if not already registered
        if not Page._feincms_templates:
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

        # Create a test Page with initial template_key='base'
        self.page = Page.objects.create(
            title="Test Page",
            slug="test-page",
            template_key="base",
            active=True,
            in_navigation=True,
        )

    def test_double_submission_protection(self):
        """
        Test that submit buttons are disabled after template change.

        This verifies the fix for Issue #677 by:
        1. Logging into the admin
        2. Navigating to a Page change view
        3. Changing the template to trigger the on_template_key_changed event
        4. Accepting the confirmation alert
        5. Verifying that the Save button is immediately disabled
        """
        # Log in to Django admin
        self.selenium.get(f"{self.live_server_url}/admin/login/")

        username_input = self.selenium.find_element(By.NAME, "username")
        password_input = self.selenium.find_element(By.NAME, "password")

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)

        login_button = self.selenium.find_element(
            By.CSS_SELECTOR, 'input[type="submit"]'
        )
        login_button.click()

        # Wait for login to complete
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#content"))
        )

        # Navigate to the Page change view
        self.selenium.get(
            f"{self.live_server_url}/admin/page/page/{self.page.pk}/change/"
        )

        # Wait for the page to load
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.NAME, "template_key"))
        )

        # Find the template key input - could be either select or radio buttons
        template_inputs = self.selenium.find_elements(By.NAME, "template_key")

        if len(template_inputs) == 1 and template_inputs[0].tag_name == "select":
            # It's a select dropdown
            select = Select(template_inputs[0])
            # Change to a different template
            current_value = select.first_selected_option.get_attribute("value")
            for option in select.options:
                if option.get_attribute("value") != current_value:
                    select.select_by_value(option.get_attribute("value"))
                    break
        else:
            # It's radio buttons
            for radio in template_inputs:
                if not radio.is_selected():
                    radio.click()
                    break

        # Wait for and accept the confirmation alert
        try:
            WebDriverWait(self.selenium, 5).until(EC.alert_is_present())
            alert = self.selenium.switch_to.alert
            alert.accept()
        except TimeoutException:
            self.fail("Expected confirmation alert did not appear")

        # CRITICAL ASSERTION: Verify that the Save button is disabled
        # This should happen immediately after accepting the alert
        try:
            save_button = self.selenium.find_element(
                By.CSS_SELECTOR, 'input[name="_save"]'
            )

            # Check if the button has the disabled attribute
            is_disabled = save_button.get_attribute("disabled")

            self.assertIsNotNone(
                is_disabled,
                "The Save button should be disabled after template change to prevent double submission",
            )
            self.assertEqual(
                is_disabled,
                "true",
                "The Save button's disabled attribute should be set to 'true'",
            )
        except Exception as e:
            self.fail(f"Failed to verify button disabled state: {e}")
