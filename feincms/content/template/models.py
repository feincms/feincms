import os

from django import forms
from django.conf import settings
from django.db import models
from django.template.loader import find_template_loader, render_to_string
from django.utils.translation import ugettext_lazy as _

from feincms.admin.editor import ItemEditorForm


def get_templates():
    seen = set()

    yield ('', '----------')

    for loader in settings.TEMPLATE_LOADERS:
        loader_instance = find_template_loader(loader)
        if not loader_instance:
            continue

        for basepath in loader_instance.get_template_sources('.'):
            path = os.path.join(basepath, 'content', 'template')
            try:
                templates = os.listdir(path)
            except (OSError, IOError):
                continue

            for template in templates:
                if template in seen:
                    continue
                if template[:4] == '.tmp':
                    continue
                seen.add(template)
                yield (template, template)


class TemplateContentAdminForm(ItemEditorForm):
    filename = forms.ChoiceField(label=_('template'))

    def __init__(self, *args, **kwargs):
        super(TemplateContentAdminForm, self).__init__(*args, **kwargs)
        self.fields['filename'].choices = sorted(get_templates(), key=lambda p: p[1])


class TemplateContent(models.Model):
    feincms_item_editor_form = TemplateContentAdminForm

    filename = models.CharField(_('template'), max_length=100,
        choices=())

    class Meta:
        abstract = True
        verbose_name = _('template content')
        verbose_name_plural = _('template contents')

    def render(self, **kwargs):
        context = kwargs.pop('context', None)

        return render_to_string('content/template/%s' % self.filename, dict({
            'content': self,
            }, **kwargs), context_instance=context)
