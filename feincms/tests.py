from django.test import TestCase

class TranslationsTest(TestCase):
    def test_short_language_code(self):
        # this is quite stupid, but it's the first time I do something
        # with TestCase

        import feincms.translations
        import doctest

        doctest.testmod(feincms.translations)


class UtilsTest(TestCase):
    def test_get_object(self):
        from feincms.utils import get_object

        self.assertRaises(AttributeError, lambda: get_object('feincms.does_not_exist'))
        self.assertRaises(ImportError, lambda: get_object('feincms.does_not_exist.fn'))

        self.assertEqual(get_object, get_object('feincms.utils.get_object'))

    def test_collect_dict_values(self):
        from feincms.utils import collect_dict_values

        self.assertEqual({'a': [1, 2], 'b': [3]},
            collect_dict_values([('a', 1), ('a', 2), ('b', 3)]))
