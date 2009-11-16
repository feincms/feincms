################################################################################
# License
################################################################################
# Copyright (c) 2007 Jeremy Whitlock.  All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import os, sys, logging
from coverage import coverage

sys.path = [os.path.join(os.path.dirname(__file__), "lib")] + sys.path

from django.test.simple import run_tests as django_test_runner
from django.conf import settings
from django.db.models import get_app, get_apps

def test_runner_with_coverage(test_labels, verbosity=1, interactive=True, extra_tests=[], html_output_dir="/tmp/nasascience"):
    """Custom test runner.  Follows the django.test.simple.run_tests() interface."""

    use_coverage = hasattr(settings, 'COVERAGE_MODULES') and len(settings.COVERAGE_MODULES)
    # If the user provided modules on the command-line we'll only test the listed modules:
    if not test_labels:
        test_labels = []

        site_name = settings.SETTINGS_MODULE.split(".")[0]

        for app in get_apps():
            pkg = app.__package__ or "" # Avoid issue with Nones
            if pkg and pkg.startswith(site_name):
                test_labels.append(pkg.split(".")[-1])

        test_labels.sort()

        logging.info("Automatically generated test labels for %s: %s", site_name, ", ".join(test_labels))


    coverage_modules = map(get_app, test_labels)

    settings.DEBUG = False

    # Start code coverage before anything else if necessary
    if use_coverage:
        cov = coverage()
        cov.use_cache(0) # Do not cache any of the coverage.py stuff
        cov.start()

    test_results = django_test_runner(test_labels, verbosity, interactive, extra_tests)

    # Stop code coverage after tests have completed
    if use_coverage:
        cov.stop()

    # Print code metrics header
    print ''
    print '-------------------------------------------------------------------------'
    print ' Unit Test Code Coverage Results'
    print '-------------------------------------------------------------------------'

    # Report code coverage metrics
    cov.report(coverage_modules)

    cov.html_report(coverage_modules, directory=html_output_dir)

    # Print code metrics footer
    print '-------------------------------------------------------------------------'

    return test_results
