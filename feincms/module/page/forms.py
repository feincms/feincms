# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

from django import forms
from django.contrib.sites.models import Site
from django.forms.models import model_to_dict
from django.forms.util import ErrorList
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms import ensure_completely_loaded

from .models import Page, PageManager

from mptt.forms import MPTTAdminForm


# ------------------------------------------------------------------------
class PageAdminForm(MPTTAdminForm):
    never_copy_fields = ('title', 'slug', 'parent', 'active', 'override_url',
        'translation_of', '_content_title', '_page_title')

    def __init__(self, *args, **kwargs):
        ensure_completely_loaded()

        if 'initial' in kwargs:
            if 'parent' in kwargs['initial']:
                # Prefill a few form values from the parent page
                try:
                    page = Page.objects.get(pk=kwargs['initial']['parent'])
                    data = model_to_dict(page)

                    for field in PageManager.exclude_from_copy:
                        if field in data:
                            del data[field]

                    # These are always excluded from prefilling
                    for field in self.never_copy_fields:
                        if field in data:
                            del data[field]

                    data.update(kwargs['initial'])
                    kwargs['initial'] = data
                except Page.DoesNotExist:
                    pass

            elif 'translation_of' in kwargs['initial']:
                # Only if translation extension is active
                try:
                    page = Page.objects.get(pk=kwargs['initial']['translation_of'])
                    original = page.original_translation

                    data = {
                        'translation_of': original.id,
                        'template_key': original.template_key,
                        'active': original.active,
                        'in_navigation': original.in_navigation,
                        }

                    if original.parent:
                        try:
                            data['parent'] = original.parent.get_translation(kwargs['initial']['language']).id
                        except Page.DoesNotExist:
                            # ignore this -- the translation does not exist
                            pass

                    data.update(kwargs['initial'])
                    kwargs['initial'] = data
                except (AttributeError, Page.DoesNotExist):
                    pass

        super(PageAdminForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            choices = []
            for key, template in kwargs['instance'].TEMPLATE_CHOICES:
                template = kwargs['instance']._feincms_templates[key]
                if template.preview_image:
                    choices.append((template.key,
                                    mark_safe(u'<img src="%s" alt="%s" /> %s' % (
                                              template.preview_image, template.key, template.title))))
                else:
                    choices.append((template.key, template.title))

            self.fields['template_key'].choices = choices

    def clean(self):
        cleaned_data = super(PageAdminForm, self).clean()

        # No need to think further, let the user correct errors first
        if self._errors:
            return cleaned_data

        current_id = None
        # See the comment below on why we do not use Page.objects.active(),
        # at least for now.
        active_pages = Page.objects.filter(active=True)

        if self.instance:
            current_id = self.instance.id
            active_pages = active_pages.exclude(id=current_id)

        if hasattr(Site, 'page_set') and 'site' in cleaned_data:
            active_pages = active_pages.filter(site=cleaned_data['site'])

        if not cleaned_data['active']:
            # If the current item is inactive, we do not need to conduct
            # further validation. Note that we only check for the flag, not
            # for any other active filters. This is because we do not want
            # to inspect the active filters to determine whether two pages
            # really won't be active at the same time.
            return cleaned_data

        if cleaned_data['override_url']:
            if active_pages.filter(_cached_url=cleaned_data['override_url']).count():
                self._errors['override_url'] = ErrorList([_('This URL is already taken by an active page.')])
                del cleaned_data['override_url']

            return cleaned_data

        if current_id:
            # We are editing an existing page
            parent = Page.objects.get(pk=current_id).parent
        else:
            # The user tries to create a new page
            parent = cleaned_data['parent']

        if parent:
            new_url = '%s%s/' % (parent._cached_url, cleaned_data['slug'])
        else:
            new_url = '/%s/' % cleaned_data['slug']

        if active_pages.filter(_cached_url=new_url).count():
            self._errors['active'] = ErrorList([_('This URL is already taken by another active page.')])
            del cleaned_data['active']

        return cleaned_data

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
