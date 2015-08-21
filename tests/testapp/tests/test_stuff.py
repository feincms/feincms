# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import doctest

from django.test import TestCase
from django.utils.encoding import force_text

import feincms
from feincms.models import Region, Template
from feincms.utils import get_object, shorten_string


# ------------------------------------------------------------------------
class Empty(object):
    """
    Helper class to use as request substitute (or whatever)
    """

    pass


class DocTest(TestCase):
    def test_translation_short_language_code(self):
        doctest.testmod(feincms.translations)

    def test_medialibrary_doctests(self):
        doctest.testmod(feincms.module.medialibrary.models)


class ModelsTest(TestCase):
    def test_region(self):
        # Creation should not fail

        r = Region('region', 'region title')
        t = Template(
            'base template',
            'base.html',
            (
                ('region', 'region title'),
                Region('region2', 'region2 title'),
            ),
        )

        # I'm not sure whether this test tests anything at all
        self.assertEqual(r.key, t.regions[0].key)
        self.assertEqual(force_text(r), 'region title')


class UtilsTest(TestCase):
    def test_get_object(self):
        self.assertRaises(
            AttributeError, lambda: get_object('feincms.does_not_exist'))
        self.assertRaises(
            ImportError, lambda: get_object('feincms.does_not_exist.fn'))

        self.assertEqual(get_object, get_object('feincms.utils.get_object'))

    def test_shorten_string(self):
        string = shorten_string(
            "Der Wolf und die Grossmutter assen im Wald zu mittag",
            15, ellipsis="_")
        self.assertEqual(string, 'Der Wolf und_ag')
        self.assertEqual(len(string), 15)

        string = shorten_string(
            "Haenschen-Klein, ging allein, in den tiefen Wald hinein",
            15)
        self.assertEqual(string, 'Haenschen \u2026 ein')
        self.assertEqual(len(string), 15)

        string = shorten_string(
            'Badgerbadgerbadgerbadgerbadger',
            10, ellipsis='-')
        self.assertEqual(string, 'Badger-ger')
        self.assertEqual(len(string), 10)
