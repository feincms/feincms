from django.db import models

from feincms.admin.item_editor import FeinCMSInline


class CustomContentType(models.Model):
    class Meta:
        abstract = True


class CategoriesContentInline(FeinCMSInline):
    filter_horizontal = ["categories"]


class CategoriesContent(models.Model):
    feincms_item_editor_inline = CategoriesContentInline

    categories = models.ManyToManyField("testapp.Category")

    class Meta:
        abstract = True

    def render(self, **kwargs):
        return ", ".join(str(category) for category in self.categories.all())
