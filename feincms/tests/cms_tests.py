# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase

from feincms.content.contactform.models import ContactFormContent
from feincms.content.file.models import FileContent
from feincms.content.image.models import ImageContent
from feincms.content.raw.models import RawContent
from feincms.content.richtext.models import RichTextContent
from feincms.content.video.models import VideoContent

from .tests import ExampleCMSBase, Empty, ExampleCMSBase2

# ------------------------------------------------------------------------
class SubRawContent(RawContent):
    title = models.CharField('title', max_length=100, blank=True)

    class Meta:
        abstract = True


class CMSBaseTest(TestCase):
    def test_01_simple_content_type_creation(self):
        self.assertEqual(ExampleCMSBase.content_type_for(FileContent), None)

        ExampleCMSBase.create_content_type(ContactFormContent)
        ExampleCMSBase.create_content_type(FileContent, regions=('region2',))

        ExampleCMSBase.create_content_type(RawContent)
        ExampleCMSBase.create_content_type(RichTextContent)

        # test creating a cotent with arguments, but no initialize_type classmethod
        ExampleCMSBase.create_content_type(VideoContent, arbitrary_arg='arbitrary_value')

        # content_type_for should return None if it does not have a subclass registered
        self.assertEqual(ExampleCMSBase.content_type_for(Empty), None)

        self.assertTrue('filecontent' not in dict(ExampleCMSBase.template.regions[0].content_types).keys())
        self.assertTrue('filecontent' in dict(ExampleCMSBase.template.regions[1].content_types).keys())

    def test_02_rsscontent_creation(self):
        # this test resides in its own method because the required feedparser
        # module is not available everywhere
        from feincms.content.rss.models import RSSContent
        type = ExampleCMSBase.create_content_type(RSSContent)
        obj = type()

        self.assertTrue('yahoo' not in obj.render())

        obj.link = 'http://rss.news.yahoo.com/rss/topstories'
        obj.cache_content(save=False)

        self.assertTrue('yahoo' in obj.render())

    #Creating a content type twice isn't forbidden anymore
    #def test_03_double_creation(self):
    #    # creating a content type twice is forbidden
    #    self.assertRaises(ImproperlyConfigured,
    #        lambda: ExampleCMSBase.create_content_type(RawContent))

    def test_04_mediafilecontent_creation(self):
        # the medialibrary needs to be enabled, otherwise this test fails

        from feincms.content.medialibrary.models import MediaFileContent

        # no TYPE_CHOICES, should raise
        self.assertRaises(ImproperlyConfigured,
                          lambda: ExampleCMSBase.create_content_type(MediaFileContent))

    def test_05_non_abstract_content_type(self):
        # Should not be able to create a content type from a non-abstract base type
        class TestContentType(models.Model):
            pass

        self.assertRaises(ImproperlyConfigured,
            lambda: ExampleCMSBase.create_content_type(TestContentType))

    def test_06_videocontent(self):
        type = ExampleCMSBase.content_type_for(VideoContent)
        obj = type()
        obj.video = 'http://www.youtube.com/watch?v=zmj1rpzDRZ0'

        self.assertTrue('x-shockwave-flash' in obj.render())

        self.assertEqual(getattr(type, 'arbitrary_arg'), 'arbitrary_value')

        obj.video = 'http://www.example.com/'

        self.assertTrue(obj.video in obj.render())

    def test_07_default_render_method(self):
        class SomethingElse(models.Model):
            class Meta:
                abstract = True

            def render_region(self):
                return 'hello'

        type = ExampleCMSBase.create_content_type(SomethingElse)
        obj = type()
        self.assertRaises(NotImplementedError, lambda: obj.render())

        obj.region = 'region'
        self.assertEqual(obj.render(), 'hello')

    def test_08_creating_two_content_types_in_same_application(self):
        ExampleCMSBase.create_content_type(RawContent)
        ct = ExampleCMSBase.content_type_for(RawContent)
        self.assertEqual(ct._meta.db_table, 'tests_examplecmsbase_rawcontent')

        ExampleCMSBase2.create_content_type(RawContent, class_name='RawContent2')
        ct2 = ExampleCMSBase2.content_type_for(RawContent)
        self.assertEqual(ct2._meta.db_table, 'tests_examplecmsbase2_rawcontent2')

    def test_09_related_objects_cache(self):
        """
        We need to define a model with relationship to our Base *after* all
        content types have been registered; previously _fill_*_cache methods
        were called during each content type registration, so any new related
        objects added after the last content type time missed the boat. Now we
        delete the cache so hopefully _fill_*_cache* won't be called until all
        related models have been defined.
        """
        class Attachment(models.Model):
            base = models.ForeignKey(ExampleCMSBase, related_name='test_related_name')

        # See issue #323 on Github.
        ExampleCMSBase._meta._fill_related_objects_cache()

        related_models = map(
            lambda x: x.model, ExampleCMSBase._meta.get_all_related_objects())

        self.assertTrue(Attachment in related_models)
        self.assertTrue(hasattr(ExampleCMSBase, 'test_related_name'))
        #self.assertFalse(hasattr(Attachment, 'anycontents'))

        class AnyContent(models.Model):
            attachment = models.ForeignKey(Attachment, related_name='anycontents')
            class Meta:
                abstract = True
        ct = ExampleCMSBase.create_content_type(AnyContent)

        self.assertTrue(hasattr(ExampleCMSBase, 'test_related_name'))
        self.assertTrue(hasattr(Attachment, 'anycontents'))

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

