"""
This extension adds a language field to every page. When calling setup_request,
the page's language is activated.
Pages in secondary languages can be said to be a translation of a page in the
primary language (the first language in settings.LANGUAGES), thereby enabling
deeplinks between translated pages...

This extension requires an activated LocaleMiddleware or something equivalent.
"""

from django.conf import settings
from django.db import models
from django.http import HttpResponseRedirect
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
        if page.language == translation.get_language():
            return

        if translation.check_for_language(page.language):
            select_language = page.language
            fallback = False
        else:
            # The page is in a language that Django has no messages for.
            # We display anyhow, but fall back to primary language for
            # other messages and other applications. It is *highly* recommended to
            # create a new django.po for the language instead of
            # using this behaviour.
            select_language = settings.LANGUAGES[0][0]
            fallback = True

        translation.activate(select_language)
        request.LANGUAGE_CODE = translation.get_language()

        if hasattr(request, 'session') and select_language != request.session.get('django_language'):
            request.session['django_language'] = select_language
        elif request.method == 'GET' and not fallback:
            # No session is active. We need to set a cookie for the language
            # so that it persists when the user changes his location to somewhere
            # not under the control of the CMS.
            # Only do this when request method is GET (mainly, do not abort
            # POST requests)
            response = HttpResponseRedirect(request.get_full_path())
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, select_language)
            return response

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
        translations = dict((p.language, p.id) for p in page.available_translations())

        links = []

        for key, title in settings.LANGUAGES:
            if key == page.language:
                continue

            if key in translations:
                links.append(u'<a href="%s/" title="%s">%s</a>' % (
                    translations[key], _('Edit translation'), key.upper()))
            else:
                links.append(u'<a style="color:#baa" href="add/?translation_of=%s&amp;language=%s" title="%s">%s</a>' % (
                    page.id, key, _('Create translation'), key.upper()))

        return u' | '.join(links)

    def original_translation(self):
        if is_primary_language(self.language):
            return self
        return self.translation_of
    cls.original_translation = property(original_translation)

    def get_translation(self, language):
        return self.original_translation.translations.get(language=language)
    cls.get_translation = get_translation

    available_translations_admin.allow_tags = True
    available_translations_admin.short_description = _('translations')
    admin_cls.available_translations_admin = available_translations_admin

    admin_cls.fieldsets[0][1]['fields'].extend(['language', 'translation_of'])
    admin_cls.list_display.extend(['language', 'available_translations_admin'])
    admin_cls.list_filter.extend(['language'])
    admin_cls.show_on_top.extend(['language'])

    admin_cls.raw_id_fields.append('translation_of')
