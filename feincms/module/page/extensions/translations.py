from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.admin import PageAdmin
from feincms.module.page.models import Page


def register():
    primary_language = settings.LANGUAGES[0][0]

    Page.add_to_class('language', models.CharField(_('language'), max_length=10,
        choices=settings.LANGUAGES))
    Page.add_to_class('translation_of', models.ForeignKey('self',
        blank=True, null=True, verbose_name='translation of',
        related_name='translations',
        limit_choices_to={'language': primary_language}))

    Page._ext_translation_setup_request = Page.setup_request
    def _setup_request(self, request):
        translation.activate(self.language)
        request.LANGUAGE_CODE = translation.get_language()
        self._ext_translation_setup_request(request)

    Page.setup_request = _setup_request

    def available_translations(self):
        if self.language==primary_language:
            return self.translations.all()
        elif self.translation_of:
            return [self.translation_of]+list(self.translation_of.translations.exclude(
                language=self.language))
        else:
            return []

    Page.available_translations = available_translations

    def available_translations_admin(self):
        translations = self.available_translations()

        return u', '.join(
            u'<a href="%s/">%s</a>' % (page.id, page.language.upper()) for page in translations)

    available_translations_admin.allow_tags = True
    available_translations_admin.short_description = _('available translations')
    Page.available_translations_admin = available_translations_admin

    PageAdmin.fieldsets[0][1]['fields'] += ('language',)
    PageAdmin.list_display += ('language', 'available_translations_admin')
