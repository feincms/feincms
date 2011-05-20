"""
This extension adds a language field to every blog entry.

Blog entries in secondary languages can be said to be a translation of a
blog entry in the primary language (the first language in settings.LANGUAGES),
thereby enabling deeplinks between translated blog entries.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


def register(cls, admin_cls):
    primary_language = settings.LANGUAGES[0][0]

    cls.add_to_class('language', models.CharField(_('language'), max_length=10,
        choices=settings.LANGUAGES))
    cls.add_to_class('translation_of', models.ForeignKey('self',
        blank=True, null=True, verbose_name=_('translation of'),
        related_name='translations',
        limit_choices_to={'language': primary_language},
        help_text=_('Leave this empty for entries in the primary language.')
        ))

    def available_translations(self):
        if self.language == primary_language:
            return self.translations.all()
        elif self.translation_of:
            return [self.translation_of] + list(self.translation_of.translations.exclude(
                language=self.language))
        else:
            return []

    cls.available_translations = available_translations

    def available_translations_admin(self):
        translations = self.available_translations()

        return u', '.join(
            u'<a href="%s/">%s</a>' % (page.id, page.language.upper()) for page in translations)

    available_translations_admin.allow_tags = True
    available_translations_admin.short_description = _('available translations')
    cls.available_translations_admin = available_translations_admin

    if getattr(admin_cls, 'fieldsets'):
        admin_cls.fieldsets[0][1]['fields'].extend(['language'])

    admin_cls.list_display += ('language', 'available_translations_admin')
    admin_cls.list_filter += ('language',)

    admin_cls.raw_id_fields.append('translation_of')
