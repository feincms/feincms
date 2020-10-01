from __future__ import absolute_import, unicode_literals

import six

from django import forms
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from feincms.content.application.models import ApplicationContent
from feincms.contents import RawContent, TemplateContent
from feincms.models import Base, create_base_model
from feincms.module.medialibrary.contents import MediaFileContent
from feincms.module.page.models import Page
from feincms.module.page import processors

from mptt.models import MPTTModel

from .content import CustomContentType

Page.register_templates(
    {
        "key": "base",
        "title": "Base Template",
        "path": "base.html",
        "regions": (("main", "Main region"), ("sidebar", "Sidebar", "inherited")),
    }
)
Page.create_content_type(RawContent)
Page.create_content_type(
    MediaFileContent, TYPE_CHOICES=(("default", "Default position"),)
)
Page.create_content_type(
    TemplateContent, TEMPLATES=[("templatecontent_1.html", "template 1")]
)
Page.register_request_processor(processors.etag_request_processor)
Page.register_response_processor(processors.etag_response_processor)
Page.register_response_processor(processors.debug_sql_queries_response_processor())


def get_admin_fields(form, *args, **kwargs):
    return {
        "exclusive_subpages": forms.BooleanField(
            label=capfirst(_("exclusive subpages")),
            required=False,
            initial=form.instance.parameters.get("exclusive_subpages", False),
            help_text=_(
                "Exclude everything other than the application's content"
                " when rendering subpages."
            ),
        ),
        "custom_field": forms.CharField(),
    }


Page.create_content_type(
    ApplicationContent,
    APPLICATIONS=(
        (
            "whatever",
            "Test Urls",
            {
                "admin_fields": get_admin_fields,
                "urls": "testapp.applicationcontent_urls",
            },
        ),
    ),
)

Page.register_extensions(
    "feincms.module.page.extensions.navigation",
    "feincms.module.page.extensions.sites",
    "feincms.extensions.translations",
    "feincms.extensions.datepublisher",
    "feincms.extensions.translations",
    "feincms.extensions.ct_tracker",
    "feincms.extensions.seo",
    "feincms.extensions.changedate",
    "feincms.extensions.seo",  # duplicate
    "feincms.module.page.extensions.navigation",
    "feincms.module.page.extensions.symlinks",
    "feincms.module.page.extensions.titles",
    "feincms.module.page.extensions.navigationgroups",
)


@six.python_2_unicode_compatible
class Category(MPTTModel):
    name = models.CharField(max_length=20)
    slug = models.SlugField()
    parent = models.ForeignKey(
        "self", blank=True, null=True, related_name="children", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["tree_id", "lft"]
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class ExampleCMSBase(Base):
    pass


ExampleCMSBase.register_regions(
    ("region", "region title"), ("region2", "region2 title")
)


class ExampleCMSBase2(Base):
    pass


ExampleCMSBase2.register_regions(
    ("region", "region title"), ("region2", "region2 title")
)


class MyModel(create_base_model()):
    pass


MyModel.register_regions(("main", "Main region"))


unchanged = CustomContentType
MyModel.create_content_type(CustomContentType)
assert CustomContentType is unchanged
