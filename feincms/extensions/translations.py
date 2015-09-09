# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

"""
This extension adds a language field to every page. When calling the request
processors the page's language is activated.
Pages in secondary languages can be said to be a translation of a page in the
primary language (the first language in settings.LANGUAGES), thereby enabling
deeplinks between translated pages.

It is recommended to activate
:class:`django.middleware.locale.LocaleMiddleware` so that the correct language
will be activated per user or session even for non-FeinCMS managed views such
as Django's administration tool.
"""

from __future__ import absolute_import, unicode_literals


# ------------------------------------------------------------------------
import logging

from django.conf import settings as django_settings
from django.db import models
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from feincms import extensions, settings
from feincms.translations import is_primary_language
from feincms._internal import monkeypatch_method, monkeypatch_property


# ------------------------------------------------------------------------
logger = logging.getLogger(__name__)
LANGUAGE_COOKIE_NAME = django_settings.LANGUAGE_COOKIE_NAME


# ------------------------------------------------------------------------
def user_has_language_set(request):
    """
    Determine whether the user has explicitely set a language earlier on.
    This is taken later on as an indication that we should not mess with the
    site's language settings, after all, the user's decision is what counts.
    """
    if (hasattr(request, 'session') and
            request.session.get(LANGUAGE_COOKIE_NAME) is not None):
        return True
    if LANGUAGE_COOKIE_NAME in request.COOKIES:
        return True
    return False


# ------------------------------------------------------------------------
def translation_allowed_language(select_language):
    "Check for feincms specific set of allowed front end languages."
    if settings.FEINCMS_FRONTEND_LANGUAGES:
        l = select_language[:2]
        if l not in settings.FEINCMS_FRONTEND_LANGUAGES:
            select_language = django_settings.LANGUAGES[0][0]

    return select_language


# ------------------------------------------------------------------------
def translation_set_language(request, select_language):
    """
    Set and activate a language, if that language is available.
    """

    select_language = translation_allowed_language(select_language)

    if translation.check_for_language(select_language):
        fallback = False
    else:
        # The page is in a language that Django has no messages for.
        # We display anyhow, but fall back to primary language for
        # other messages and other applications. It is *highly* recommended to
        # create a new django.po for the language instead of
        # using this behaviour.
        select_language = django_settings.LANGUAGES[0][0]
        fallback = True

    translation.activate(select_language)
    request.LANGUAGE_CODE = translation.get_language()

    if hasattr(request, 'session'):
        # User has a session, then set this language there
        if select_language != request.session.get(LANGUAGE_COOKIE_NAME):
            request.session[LANGUAGE_COOKIE_NAME] = select_language
    elif request.method == 'GET' and not fallback:
        # No session is active. We need to set a cookie for the language
        # so that it persists when users change their location to somewhere
        # not under the control of the CMS.
        # Only do this when request method is GET (mainly, do not abort
        # POST requests)
        response = HttpResponseRedirect(request.get_full_path())
        response.set_cookie(
            str(LANGUAGE_COOKIE_NAME), select_language)
        return response


# ------------------------------------------------------------------------
def translations_request_processor_explicit(page, request):
    # If this page is just a redirect, don't do any language specific setup
    if page.redirect_to:
        return

    # Until further notice, the user might be wanting to switch to the
    # page's language...
    desired_language = page.language

    # ...except if the user explicitely wants to switch language
    if 'set_language' in request.GET:
        desired_language = request.GET['set_language']
    # ...or the user already has explicitely set a language, bail out and
    # don't change it for them behind their back
    elif user_has_language_set(request):
        return

    return translation_set_language(request, desired_language)


# ------------------------------------------------------------------------
def translations_request_processor_standard(page, request):
    # If this page is just a redirect, don't do any language specific setup
    if getattr(page, 'redirect_to', None):
        return

    if page.language == translation.get_language():
        return

    return translation_set_language(request, page.language)


# ------------------------------------------------------------------------
def get_current_language_code(request):
    language_code = getattr(request, 'LANGUAGE_CODE', None)
    if language_code is None:
        logger.warning(
            "Could not access request.LANGUAGE_CODE. Is 'django.middleware."
            "locale.LocaleMiddleware' in MIDDLEWARE_CLASSES?")
    return language_code


# ------------------------------------------------------------------------
class Extension(extensions.Extension):

    def handle_model(self):
        cls = self.model

        cls.add_to_class(
            'language',
            models.CharField(
                _('language'),
                max_length=10,
                choices=django_settings.LANGUAGES,
                default=django_settings.LANGUAGES[0][0]))
        cls.add_to_class(
            'translation_of',
            models.ForeignKey(
                'self',
                blank=True, null=True, verbose_name=_('translation of'),
                related_name='translations',
                limit_choices_to={'language': django_settings.LANGUAGES[0][0]},
                help_text=_(
                    'Leave this empty for entries in the primary language.'),
            )
        )

        if hasattr(cls, 'register_request_processor'):
            if settings.FEINCMS_TRANSLATION_POLICY == "EXPLICIT":
                cls.register_request_processor(
                    translations_request_processor_explicit,
                    key='translations')
            else:  # STANDARD
                cls.register_request_processor(
                    translations_request_processor_standard,
                    key='translations')

        if hasattr(cls, 'get_redirect_to_target'):
            original_get_redirect_to_target = cls.get_redirect_to_target

            @monkeypatch_method(cls)
            def get_redirect_to_target(self, request):
                """
                Find an acceptable redirect target. If this is a local link,
                then try to find the page this redirect references and
                translate it according to the user's language. This way, one
                can easily implement a localized "/"-url to welcome page
                redirection.
                """
                target = original_get_redirect_to_target(self, request)
                if target and target.find('//') == -1:
                    # Not an offsite link http://bla/blubb
                    try:
                        page = cls.objects.page_for_path(target)
                        language = get_current_language_code(request)
                        language = translation_allowed_language(language)
                        page = page.get_translation(language)
                        # Note: Does not care about active status?
                        target = page.get_absolute_url()
                    except cls.DoesNotExist:
                        pass
                return target

        @monkeypatch_method(cls)
        def available_translations(self):
            if not self.id:  # New, unsaved pages have no translations
                return []

            if hasattr(cls.objects, 'apply_active_filters'):
                filter_active = cls.objects.apply_active_filters
            else:
                def filter_active(queryset):
                    return queryset

            if is_primary_language(self.language):
                return filter_active(self.translations.all())
            elif self.translation_of:
                # reuse prefetched queryset, do not filter it
                res = [
                    t for t
                    in filter_active(self.translation_of.translations.all())
                    if t.language != self.language]
                res.insert(0, self.translation_of)
                return res
            else:
                return []

        @monkeypatch_method(cls)
        def get_original_translation(self, *args, **kwargs):
            if is_primary_language(self.language):
                return self
            if self.translation_of:
                return self.translation_of
            logger.debug(
                "Page pk=%d (%s) has no primary language translation (%s)",
                self.pk, self.language, django_settings.LANGUAGES[0][0])
            return self

        @monkeypatch_property(cls)
        def original_translation(self):
            return self.get_original_translation()

        @monkeypatch_method(cls)
        def get_translation(self, language):
            return self.original_translation.translations.get(
                language=language)

    def handle_modeladmin(self, modeladmin):
        extensions.prefetch_modeladmin_get_queryset(
            modeladmin, 'translation_of__translations', 'translations')

        def available_translations_admin(self, page):
            # Do not use available_translations() because we don't care
            # whether pages are active or not here.
            translations = [page]
            translations.extend(page.translations.all())
            if page.translation_of:
                translations.append(page.translation_of)
                translations.extend(page.translation_of.translations.all())
            translations = {
                p.language: p.id
                for p in translations
            }

            links = []

            for key, title in django_settings.LANGUAGES:
                if key == page.language:
                    continue

                if key in translations:
                    links.append('<a href="%s/" title="%s">%s</a>' % (
                        translations[key], _('Edit translation'), key.upper()))
                else:
                    links.append(
                        '<a style="color:#baa" href="add/?translation_of='
                        '%s&amp;language=%s" title="%s">%s</a>' % (
                            page.id,
                            key,
                            _('Create translation'),
                            key.upper()
                        )
                    )

            return ' | '.join(links)

        available_translations_admin.allow_tags = True
        available_translations_admin.short_description = _('translations')
        modeladmin.__class__.available_translations_admin =\
            available_translations_admin

        if hasattr(modeladmin, 'add_extension_options'):
            modeladmin.add_extension_options('language', 'translation_of')

        modeladmin.extend_list(
            'list_display',
            ['language', 'available_translations_admin'],
        )
        modeladmin.extend_list('list_filter', ['language'])
        modeladmin.extend_list('raw_id_fields', ['translation_of'])

# ------------------------------------------------------------------------
