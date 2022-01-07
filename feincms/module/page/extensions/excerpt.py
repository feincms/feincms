"""
Add an excerpt field to the page.
"""


from django.db import models
from django.utils.translation import gettext_lazy as _

from feincms import extensions


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class(
            "excerpt",
            models.TextField(
                _("excerpt"),
                blank=True,
                help_text=_(
                    "Add a brief excerpt summarizing the content" " of this page."
                ),
            ),
        )

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options(
            _("Excerpt"), {"fields": ("excerpt",), "classes": ("collapse",)}
        )
