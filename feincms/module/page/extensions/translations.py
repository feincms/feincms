"""
This extension adds a language field to every page. When calling setup_request,
the page's language is activated.
Pages in secondary languages can be said to be a translation of a page in the
primary language (the first language in settings.LANGUAGES), thereby enabling
deeplinks between translated pages...
"""

from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from feincms.translations import is_primary_language


def register(cls, admin_cls):
    cls.add_to_class('language', models.CharField(_('language'), max_length=10,
        choices=settings.LANGUAGES))
    cls.add_to_class('translation_of', models.ForeignKey('self',
        blank=True, null=True, verbose_name=_('translation of'),
        related_name='translations',
        limit_choices_to={'language': settings.LANGUAGES[0][0]},
        help_text=_('Leave this empty for entries in the primary language (%s).') % \
            _(settings.LANGUAGES[0][1])))

    def translations_request_processor(page, request):
        translation.activate(page.language)
        request.LANGUAGE_CODE = translation.get_language()

        if hasattr(request, 'session') and request.LANGUAGE_CODE != request.session.get('django_language'):
            request.session['django_language'] = request.LANGUAGE_CODE

    cls.register_request_processors(translations_request_processor)

    def available_translations(self):
        if is_primary_language(self.language):
            return self.translations.all()
        elif self.translation_of:
            return [self.translation_of] + list(self.translation_of.translations.exclude(
                language=self.language))
        else:
            return []

    cls.available_translations = available_translations

    def available_translations_admin(self, page):
        translations = page.available_translations()

        return u', '.join(
            u'<a href="%s/" title="%s">%s</a>' % (page.id, unicode(page), page.language.upper()) for page in translations)

    def original_translation(self):
        if is_primary_language(self.language):
            return self
        return self.translation_of
    cls.original_translation = property(original_translation)

    available_translations_admin.allow_tags = True
    available_translations_admin.short_description = _('translations')
    admin_cls.available_translations_admin = available_translations_admin

    admin_cls.fieldsets[0][1]['fields'] += ('language',)
    admin_cls.list_display += ('language', 'available_translations_admin')
    admin_cls.show_on_top += ('language',)

    admin_cls.raw_id_fields.append('translation_of')
