"""
Sometimes, a single title is not enough, you'd like subtitles, and maybe
differing titles in the navigation and in the <title>-tag.  This extension lets
you do that.
"""

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms._internal import monkeypatch_property


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class('_content_title', models.TextField(
            _('content title'),
            blank=True,
            help_text=_(
                'The first line is the main title, the following'
                ' lines are subtitles.')))

        self.model.add_to_class('_page_title', models.CharField(
            _('page title'),
            max_length=69,
            blank=True,
            help_text=_(
                'Page title for browser window. Same as title by'
                'default. Must not be longer than 70 characters.')))

        @monkeypatch_property(self.model)
        def page_title(self):
            """
            Use this for the browser window (<title>-tag in the <head> of the
            HTML document)
            """

            if self._page_title:
                return self._page_title
            return self.content_title

        @monkeypatch_property(self.model)
        def content_title(self):
            """
            This should be used f.e. for the <h1>-tag
            """

            if not self._content_title:
                return self.title

            return self._content_title.splitlines()[0]

        @monkeypatch_property(self.model)
        def content_subtitle(self):
            return '\n'.join(self._content_title.splitlines()[1:])

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options(_('Titles'), {
            'fields': ('_content_title', '_page_title'),
            'classes': ('collapse',),
        })
