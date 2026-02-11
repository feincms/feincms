"""Pytest configuration for FeinCMS tests."""

import os
import sys

import django


# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def pytest_configure(config):
    """Configure Django settings for pytest."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")
    django.setup()

    # Register custom pytest markers
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test (using Playwright)"
    )
