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

import os, shutil, sys, unittest

sys.path = [os.path.join(os.path.dirname(__file__), "lib")] + sys.path

import coverage
from django.test.simple import run_tests as django_test_runner

from django.conf import settings

def test_runner_with_coverage(test_labels, verbosity=1, interactive=True, extra_tests=[]):
  """Custom test runner.  Follows the django.test.simple.run_tests() interface."""
  # Start code coverage before anything else if necessary
  if hasattr(settings, 'COVERAGE_MODULES') and not test_labels:
    coverage.use_cache(0) # Do not cache any of the coverage.py stuff
    coverage.start()

  test_results = django_test_runner(test_labels, verbosity, interactive, extra_tests)

  # Stop code coverage after tests have completed
  if hasattr(settings, 'COVERAGE_MODULES') and not test_labels:
    coverage.stop()

    # Print code metrics header
    print ''
    print '----------------------------------------------------------------------'
    print ' Unit Test Code Coverage Results'
    print '----------------------------------------------------------------------'

  # Report code coverage metrics
  if hasattr(settings, 'COVERAGE_MODULES') and not test_labels:
    coverage_modules = []
    for module in settings.COVERAGE_MODULES:
      coverage_modules.append(__import__(module, globals(), locals(), ['']))

    coverage.report(coverage_modules, show_missing=1)
    
    # Print code metrics footer
    print '----------------------------------------------------------------------'

  return test_results

# test_runner_with_coverage()
