"""
This extension adds a language field to every blog entry.

Blog entries in secondary languages can be said to be a translation of a
blog entry in the primary language (the first language in settings.LANGUAGES),
thereby enabling deeplinks between translated blog entries.
"""

from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions


class Extension(extensions.Extension):
    def handle_model(self):
        primary_language = settings.LANGUAGES[0][0]

        self.model.add_to_class(
            'language',
            models.CharField(
                _('language'),
                max_length=10,
                choices=settings.LANGUAGES,
            )
        )
        self.model.add_to_class(
            'translation_of',
            models.ForeignKey(
                'self',
                blank=True, null=True,
                verbose_name=_('translation of'),
                related_name='translations',
                limit_choices_to={'language': primary_language},
                help_text=_(
                    'Leave this empty for entries in the primary language.'),
            )
        )

        def available_translations(self):
            if self.language == primary_language:
                return self.translations.all()
            elif self.translation_of:
                return [self.translation_of] + list(
                    self.translation_of.translations.exclude(
                        language=self.language))
            else:
                return []

        self.model.available_translations = available_translations

        def available_translations_admin(self):
            translations = self.available_translations()

            return ', '.join(
                '<a href="%s/">%s</a>' % (
                    page.id,
                    page.language.upper()
                ) for page in translations
            )

        available_translations_admin.allow_tags = True
        available_translations_admin.short_description =\
            _('available translations')
        self.model.available_translations_admin = available_translations_admin

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options('language')

        modeladmin.list_display.extend((
            'language', 'available_translations_admin'))
        modeladmin.list_filter.extend(('language',))

        modeladmin.raw_id_fields.append('translation_of')
