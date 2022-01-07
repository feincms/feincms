"""
Add a "featured" field to objects so admins can better direct top content.
"""


from django.db import models
from django.utils.translation import gettext_lazy as _

from feincms import extensions


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class(
            "featured", models.BooleanField(_("featured"), default=False)
        )

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options(
            _("Featured"), {"fields": ("featured",), "classes": ("collapse",)}
        )
