from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.admin import PageAdmin
from feincms.module.page.models import Page


def register():
    Page.add_to_class('language', models.CharField(_('language'), max_length=10,
        choices=settings.LANGUAGES))
    Page.add_to_class('translations', models.ManyToManyField('self', blank=True))

    Page._ext_translation_setup_request = Page.setup_request
    def _setup_request(self, request):
        translation.activate(self.language)
        request.LANGUAGE_CODE = translation.get_language()
        self._ext_translation_setup_request(request)

    Page.setup_request = _setup_request

    PageAdmin.fieldsets[0][1]['fields'] += ('language',)
    PageAdmin.list_display += ('language',)
    PageAdmin.list_filter += ('language',)

