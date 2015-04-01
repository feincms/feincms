from __future__ import absolute_import, unicode_literals

import os

from django.db import models
from django.template.loader import (
    Context, Template, TemplateDoesNotExist, find_template_loader)
from django.utils.translation import ugettext_lazy as _


DEFAULT_TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)


class TemplateChoices(object):
    def __init__(self, template_loaders):
        self.template_loaders = template_loaders

    def __iter__(self):
        seen = set()

        for loader in self.template_loaders:
            for basepath in loader.get_template_sources('.'):
                path = os.path.join(basepath, 'content', 'template')
                try:
                    templates = os.listdir(path)
                except (OSError, IOError):
                    continue

                for template in templates:
                    if template in seen:
                        continue
                    if template.endswith(('~', '.tmp')):
                        continue
                    seen.add(template)

        return ((t, t) for t in sorted(seen))


class TemplateContent(models.Model):
    """
    This content type scans all template folders for files in the
    ``content/template/`` folder and lets the website administrator select
    any template from a set of provided choices.

    The templates aren't restricted in any way.
    """

    class Meta:
        abstract = True
        verbose_name = _('template content')
        verbose_name_plural = _('template contents')

    template_loaders = []

    @classmethod
    def initialize_type(cls, TEMPLATE_LOADERS=DEFAULT_TEMPLATE_LOADERS,
                        TEMPLATE_PATH='content/template'):
        cls.template_path = TEMPLATE_PATH
        for loader in TEMPLATE_LOADERS:
            if loader:
                # With Django 1.6 find_template_loader blows up during
                # syncdb, probably because component initialization order
                # has changed. Work around by ignoring exceptions here,
                # but of course, this will also swallow legitimate
                # exceptions. Tough luck :-(
                try:
                    cls.template_loaders.append(find_template_loader(loader))
                except Exception:
                    pass

        cls.add_to_class('filename', models.CharField(
            _('template'), max_length=100,
            choices=TemplateChoices(cls.template_loaders)))

    def render(self, **kwargs):
        context = kwargs.pop('context', None)
        name = os.path.join(self.template_path, self.filename)

        for loader in self.template_loaders:
            try:
                template, display_name = loader.load_template(name)
            except TemplateDoesNotExist:
                continue

            if not hasattr(template, 'render'):
                template = Template(template, name=name)

            if context:
                ctx = context
                ctx.update(dict(content=self, **kwargs))
            else:
                ctx = Context(dict(content=self, **kwargs))

            result = template.render(ctx)

            if context:
                context.pop()

            return result

        return ''
