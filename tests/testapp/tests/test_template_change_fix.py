"""
Tests for the template change double submission fix.

This test verifies that the JavaScript fix is in place and hasn't been accidentally removed.
"""

import os
from django.conf import settings
from django.test import TestCase


class TemplateChangeFixTest(TestCase):
    """Test that the double submission fix is present in the JavaScript file."""

    def test_fix_is_present_in_javascript(self):
        """Verify that the fix line exists in item_editor.js"""
        # Use BASEDIR from settings to construct the path
        js_file_path = os.path.join(
            settings.BASEDIR, '..', '..', 'feincms', 'static', 'feincms', 'item_editor.js'
        )
        js_file_path = os.path.normpath(js_file_path)

        # Read the file
        with open(js_file_path, "r") as f:
            content = f.read()

        # Check that the fix is present
        self.assertIn(
            'form_element.find("input[type=submit], button").attr("disabled", "disabled")',
            content,
            "The double submission fix should be present in item_editor.js",
        )

        # Verify it's in the correct context (after the click() call)
        self.assertIn(
            'form_element.find("[type=submit][name=_save]").click()',
            content,
            "The save button click trigger should be present",
        )

        # Verify the comment is present
        self.assertIn(
            "Disable all submit buttons to prevent double submission",
            content,
            "The explanatory comment should be present",
        )

    def test_fix_order_is_correct(self):
        """Verify that the disable happens AFTER the click, not before."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        js_file_path = os.path.join(
            base_dir, 'feincms', 'static', 'feincms', 'item_editor.js'
        )
        js_file_path = os.path.normpath(js_file_path)

        with open(js_file_path, "r") as f:
            content = f.read()

        # Find positions of both statements
        click_pos = content.find('form_element.find("[type=submit][name=_save]").click()')
        disable_pos = content.find('form_element.find("input[type=submit]").attr("disabled", "disabled")')

        self.assertGreater(click_pos, 0, "The click() statement should be present")
        self.assertGreater(disable_pos, 0, "The disable statement should be present")
        self.assertLess(
            click_pos,
            disable_pos,
            "The disable statement should come AFTER the click() statement",
        )
