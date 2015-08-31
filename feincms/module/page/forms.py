# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import re

from django.apps import apps
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.forms.models import model_to_dict
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms import ensure_completely_loaded

from mptt.forms import MPTTAdminForm


class RedirectToWidget(ForeignKeyRawIdWidget):
    def label_for_value(self, value):
        match = re.match(
            # XXX this regex would be available as .models.REDIRECT_TO_RE
            r'^(?P<app_label>\w+).(?P<model_name>\w+):(?P<pk>\d+)$',
            value)

        if match:
            matches = match.groupdict()
            model = apps.get_model(matches['app_label'], matches['model_name'])
            try:
                instance = model._default_manager.get(pk=int(matches['pk']))
                return '&nbsp;<strong>%s (%s)</strong>' % (
                    instance, instance.get_absolute_url())

            except model.DoesNotExist:
                pass

        return ''


# ------------------------------------------------------------------------
class PageAdminForm(MPTTAdminForm):
    never_copy_fields = (
        'title', 'slug', 'parent', 'active', 'override_url',
        'translation_of', '_content_title', '_page_title')

    @property
    def page_model(self):
        return self._meta.model

    @property
    def page_manager(self):
        return self.page_model._default_manager

    def __init__(self, *args, **kwargs):
        ensure_completely_loaded()

        if 'initial' in kwargs:
            if 'parent' in kwargs['initial']:
                # Prefill a few form values from the parent page
                try:
                    page = self.page_manager.get(
                        pk=kwargs['initial']['parent'])

                    data = model_to_dict(page)

                    for field in self.page_manager.exclude_from_copy:
                        if field in data:
                            del data[field]

                    # These are always excluded from prefilling
                    for field in self.never_copy_fields:
                        if field in data:
                            del data[field]

                    data.update(kwargs['initial'])
                    if page.template.child_template:
                        data['template_key'] = page.template.child_template
                    kwargs['initial'] = data
                except self.page_model.DoesNotExist:
                    pass

            elif 'translation_of' in kwargs['initial']:
                # Only if translation extension is active
                try:
                    page = self.page_manager.get(
                        pk=kwargs['initial']['translation_of'])
                    original = page.original_translation

                    data = {
                        'translation_of': original.id,
                        'template_key': original.template_key,
                        'active': original.active,
                        'in_navigation': original.in_navigation,
                    }

                    if original.parent:
                        try:
                            data['parent'] = original.parent.get_translation(
                                kwargs['initial']['language']
                            ).id
                        except self.page_model.DoesNotExist:
                            # ignore this -- the translation does not exist
                            pass

                    data.update(kwargs['initial'])
                    kwargs['initial'] = data
                except (AttributeError, self.page_model.DoesNotExist):
                    pass

        # Not required, only a nice-to-have for the `redirect_to` field
        modeladmin = kwargs.pop('modeladmin', None)
        super(PageAdminForm, self).__init__(*args, **kwargs)
        if modeladmin and 'redirect_to' in self.fields:
            # Note: Using `parent` is not strictly correct, but we can be
            # sure that `parent` always points to another page instance,
            # and that's good enough for us.
            self.fields['redirect_to'].widget = RedirectToWidget(
                self.page_model._meta.get_field('parent').rel,
                modeladmin.admin_site)

        if 'template_key' in self.fields:
            choices = []
            for key, template_name in self.page_model.TEMPLATE_CHOICES:
                template = self.page_model._feincms_templates[key]
                pages_for_template = self.page_model._default_manager.filter(
                    template_key=key)
                pk = kwargs['instance'].pk if kwargs.get('instance') else None
                other_pages_for_template = pages_for_template.exclude(pk=pk)
                if template.singleton and other_pages_for_template.exists():
                    continue  # don't allow selection of singleton if in use
                if template.preview_image:
                    choices.append((
                        template.key,
                        mark_safe('<img src="%s" alt="%s" /> %s' % (
                            template.preview_image,
                            template.key,
                            template.title,
                        ))
                    ))
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
        active_pages = self.page_manager.filter(active=True)

        if self.instance:
            current_id = self.instance.id
            active_pages = active_pages.exclude(id=current_id)

        sites_is_installed = apps.is_installed('django.contrib.sites')
        if sites_is_installed and 'site' in cleaned_data:
            active_pages = active_pages.filter(site=cleaned_data['site'])

        # Convert PK in redirect_to field to something nicer for the future
        redirect_to = cleaned_data.get('redirect_to')
        if redirect_to and re.match(r'^\d+$', redirect_to):
            opts = self.page_model._meta
            cleaned_data['redirect_to'] = '%s.%s:%s' % (
                opts.app_label, opts.model_name, redirect_to)

        if 'active' in cleaned_data and not cleaned_data['active']:
            # If the current item is inactive, we do not need to conduct
            # further validation. Note that we only check for the flag, not
            # for any other active filters. This is because we do not want
            # to inspect the active filters to determine whether two pages
            # really won't be active at the same time.
            return cleaned_data

        if 'override_url' in cleaned_data and cleaned_data['override_url']:
            if active_pages.filter(
                    _cached_url=cleaned_data['override_url']).count():
                self._errors['override_url'] = self.error_class([
                    _('This URL is already taken by an active page.')])
                del cleaned_data['override_url']

            return cleaned_data

        if current_id:
            # We are editing an existing page
            parent = self.page_manager.get(pk=current_id).parent
        else:
            # The user tries to create a new page
            parent = cleaned_data['parent']

        if parent:
            new_url = '%s%s/' % (parent._cached_url, cleaned_data['slug'])
        else:
            new_url = '/%s/' % cleaned_data['slug']

        if active_pages.filter(_cached_url=new_url).count():
            self._errors['active'] = self.error_class([
                _('This URL is already taken by another active page.')])
            del cleaned_data['active']

        if parent and parent.template.enforce_leaf:
            self._errors['parent'] = self.error_class(
                [_('This page does not allow attachment of child pages')])
            del cleaned_data['parent']

        return cleaned_data

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
