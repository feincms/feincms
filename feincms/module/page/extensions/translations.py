"""
This extension adds a language field to every page. When calling setup_request,
the page's language is activated.
Pages in secondary languages can be said to be a translation of a page in the
primary language (the first language in settings.LANGUAGES), thereby enabling
deeplinks between translated pages...

This extension requires an activated LocaleMiddleware or something equivalent.
"""

# ------------------------------------------------------------------------
from django.conf import settings as django_settings
from django.db import models
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.translations import is_primary_language
from feincms._internal import monkeypatch_method, monkeypatch_property

# ------------------------------------------------------------------------
def user_has_language_set(request):
    """
    Determine whether the user has explicitely set a language earlier on.
    This is taken later on as an indication that we should not mess with the
    site's language settings, after all, the user's decision is what counts.
    """
    if hasattr(request, 'session') and request.session.get('django_language') is not None:
        return True
    if django_settings.LANGUAGE_COOKIE_NAME in request.COOKIES:
        return True
    return False

# ------------------------------------------------------------------------
def translation_set_language(request, select_language):
    """
    Set and activate a language, if that language is available.
    """
    if translation.check_for_language(select_language):
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

    if hasattr(request, 'session'):
        # User has a session, then set this language there
        if select_language != request.session.get('django_language'):
            request.session['django_language'] = select_language
    elif request.method == 'GET' and not fallback:
        # No session is active. We need to set a cookie for the language
        # so that it persists when the user changes his location to somewhere
        # not under the control of the CMS.
        # Only do this when request method is GET (mainly, do not abort
        # POST requests)
        response = HttpResponseRedirect(request.get_full_path())
        response.set_cookie(django_settings.LANGUAGE_COOKIE_NAME, select_language)
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
    # don't change it for him behind her back
    elif user_has_language_set(request):
        return

    return translation_set_language(request, desired_language)

# ------------------------------------------------------------------------
def translations_request_processor_standard(page, request):
    # If this page is just a redirect, don't do any language specific setup
    if page.redirect_to:
        return

    if page.language == translation.get_language():
        return

    return translation_set_language(request, page.language)

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
def register(cls, admin_cls):
    cls.add_to_class('language', models.CharField(_('language'), max_length=10,
        choices=django_settings.LANGUAGES, default=django_settings.LANGUAGES[0][0]))
    cls.add_to_class('translation_of', models.ForeignKey('self',
        blank=True, null=True, verbose_name=_('translation of'),
        related_name='translations',
        limit_choices_to={'language': django_settings.LANGUAGES[0][0]},
        help_text=_('Leave this empty for entries in the primary language.')
        ))

    if settings.FEINCMS_TRANSLATION_POLICY == "EXPLICIT":
        cls.register_request_processors(translations_request_processor_explicit)
    else: # STANDARD
        cls.register_request_processors(translations_request_processor_standard)

    @monkeypatch_method(cls)
    def get_redirect_to_target(self, request):
        """
        Find an acceptable redirect target. If this is a local link, then try
        to find the page this redirect references and translate it according
        to the user's language. This way, one can easily implement a localized
        "/"-url to welcome page redirection.
        """
        target = self.redirect_to
        if target and target.find('//') == -1: # Not an offsite link http://bla/blubb
            try:
                page = cls.objects.page_for_path(target)
                page = page.get_translation(getattr(request, 'LANGUAGE_CODE', None))
                target = page.get_absolute_url()
            except cls.DoesNotExist:
                pass
        return target

    @monkeypatch_method(cls)
    def available_translations(self):
        if not self.id: # New, unsaved pages have no translations
            return []
        if is_primary_language(self.language):
            return self.translations.all()
        elif self.translation_of:
            return [self.translation_of] + list(self.translation_of.translations.exclude(
                language=self.language))
        else:
            return []

    @monkeypatch_method(cls)
    def get_original_translation(self, *args, **kwargs):
        if is_primary_language(self.language):
            return self
        return self.translation_of

    @monkeypatch_property(cls)
    def original_translation(self):
        return self.get_original_translation()

    @monkeypatch_method(cls)
    def get_translation(self, language):
        return self.original_translation.translations.get(language=language)

    def available_translations_admin(self, page):
        translations = dict((p.language, p.id) for p in page.available_translations())

        links = []

        for key, title in django_settings.LANGUAGES:
            if key == page.language:
                continue

            if key in translations:
                links.append(u'<a href="%s/" title="%s">%s</a>' % (
                    translations[key], _('Edit translation'), key.upper()))
            else:
                links.append(u'<a style="color:#baa" href="add/?translation_of=%s&amp;language=%s" title="%s">%s</a>' % (
                    page.id, key, _('Create translation'), key.upper()))

        return u' | '.join(links)

    available_translations_admin.allow_tags = True
    available_translations_admin.short_description = _('translations')
    admin_cls.available_translations_admin = available_translations_admin

    admin_cls.fieldsets[0][1]['fields'].extend(['language', 'translation_of'])
    admin_cls.list_display.extend(['language', 'available_translations_admin'])
    admin_cls.list_filter.extend(['language'])

    admin_cls.raw_id_fields.append('translation_of')

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
