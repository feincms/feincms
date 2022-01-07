from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase
from testapp.models import ExampleCMSBase, ExampleCMSBase2

from feincms.contents import RawContent, RichTextContent
from feincms.module.medialibrary.contents import MediaFileContent

from .test_stuff import Empty


# ------------------------------------------------------------------------
class SubRawContent(RawContent):
    title = models.CharField("title", max_length=100, blank=True)

    class Meta:
        abstract = True


class CMSBaseTest(TestCase):
    def test_01_simple_content_type_creation(self):
        self.assertEqual(ExampleCMSBase.content_type_for(RawContent), None)

        ExampleCMSBase.create_content_type(RawContent, regions=("main2",))
        ExampleCMSBase.create_content_type(RichTextContent)

        # content_type_for should return None if it does not have a subclass
        # registered
        self.assertEqual(ExampleCMSBase.content_type_for(Empty), None)

        self.assertTrue(
            "rawcontent"
            not in dict(ExampleCMSBase.template.regions[0].content_types).keys()
        )

    def test_04_mediafilecontent_creation(self):
        # the medialibrary needs to be enabled, otherwise this test fails

        # no TYPE_CHOICES, should raise
        self.assertRaises(
            ImproperlyConfigured,
            lambda: ExampleCMSBase.create_content_type(MediaFileContent),
        )

    def test_05_non_abstract_content_type(self):
        # Should not be able to create a content type from a non-abstract base
        # type
        class TestContentType(models.Model):
            pass

        self.assertRaises(
            ImproperlyConfigured,
            lambda: ExampleCMSBase.create_content_type(TestContentType),
        )

    def test_07_default_render_method(self):
        class SomethingElse(models.Model):
            class Meta:
                abstract = True

            def render_region(self):
                return "hello"

        type = ExampleCMSBase.create_content_type(SomethingElse)
        obj = type()
        self.assertRaises(NotImplementedError, lambda: obj.render())

        obj.region = "region"
        self.assertEqual(obj.render(), "hello")

    def test_08_creating_two_content_types_in_same_application(self):
        ExampleCMSBase.create_content_type(RawContent)
        ct = ExampleCMSBase.content_type_for(RawContent)
        self.assertEqual(ct._meta.db_table, "testapp_examplecmsbase_rawcontent")

        ExampleCMSBase2.create_content_type(RawContent, class_name="RawContent2")
        ct2 = ExampleCMSBase2.content_type_for(RawContent)
        self.assertEqual(ct2._meta.db_table, "testapp_examplecmsbase2_rawcontent2")

    def test_10_content_type_subclasses(self):
        """
        See:
        https://github.com/feincms/feincms/issues/339
        """
        ExampleCMSBase.create_content_type(SubRawContent)
        ExampleCMSBase.create_content_type(RawContent)

        ct = ExampleCMSBase.content_type_for(RawContent)
        ct2 = ExampleCMSBase.content_type_for(SubRawContent)
        self.assertNotEqual(ct, ct2)
