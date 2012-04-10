#!/usr/bin/env python
import os, sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testapp.settings")
    os.environ.setdefault("FEINCMS_RUN_TESTS", "1")

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
