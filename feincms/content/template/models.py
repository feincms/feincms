from django.db import models
from django.utils.translation import gettext_lazy as _

from feincms.content.raw.models import RawContent  # noqa
from feincms.content.richtext.models import RichTextContent  # noqa
from feincms.utils.tuple import AutoRenderTuple


class TemplateContent(models.Model):
    """
    Pass a list of templates when creating this content type. It uses the
    default template system::

        Page.create_content_type(TemplateContent, TEMPLATES=[
            ('content/template/something1.html', 'something'),
            ('content/template/something2.html', 'something else'),
            ('base.html', 'makes no sense'),
        ])
    """

    class Meta:
        abstract = True
        verbose_name = _("template content")
        verbose_name_plural = _("template contents")

    @classmethod
    def initialize_type(cls, TEMPLATES):
        cls.add_to_class(
            "template",
            models.CharField(_("template"), max_length=100, choices=TEMPLATES),
        )

    def render(self, **kwargs):
        return AutoRenderTuple((self.template, {"content": self}))
