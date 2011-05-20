# -*- coding: utf-8 -*-
from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

import coverage


class CoverageRunner(DjangoTestSuiteRunner):
    def run_tests(self, *args, **kwargs):
        run_with_coverage = hasattr(settings, 'COVERAGE_MODULES')

        if run_with_coverage:
            coverage.use_cache(0)
            coverage.start()

        result = super(CoverageRunner, self).run_tests(*args, **kwargs)

        if run_with_coverage:
            coverage.stop()
            print ''
            print '----------------------------------------------------------------------'
            print ' Unit Test Code Coverage Results'
            print '----------------------------------------------------------------------'
            coverage_modules = []
            for module in settings.COVERAGE_MODULES:
                coverage_modules.append(__import__(module, globals(),
                                                   locals(), ['']))
            coverage.report(coverage_modules, show_missing=1)
            print '----------------------------------------------------------------------'

        return result
