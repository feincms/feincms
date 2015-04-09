from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.admin.item_editor import ItemEditorForm
from feincms.contrib.richtext import RichTextField
from feincms.utils import get_object


class RichTextContentAdminForm(ItemEditorForm):
    #: If FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE allows, we'll convert this into
    # a checkbox so the user can choose whether to ignore HTML validation
    # warnings instead of fixing them:
    seen_tidy_warnings = forms.BooleanField(
        required=False,
        label=_("HTML Tidy"),
        help_text=_("Ignore the HTML validation warnings"),
        widget=forms.HiddenInput
    )

    def clean(self):
        cleaned_data = super(RichTextContentAdminForm, self).clean()

        if settings.FEINCMS_TIDY_HTML:
            text, errors, warnings = get_object(
                settings.FEINCMS_TIDY_FUNCTION)(cleaned_data['text'])

            # Ick, but we need to be able to update text and seen_tidy_warnings
            self.data = self.data.copy()

            # We always replace the HTML with the tidied version:
            cleaned_data['text'] = text
            self.data['%s-text' % self.prefix] = text

            if settings.FEINCMS_TIDY_SHOW_WARNINGS and (errors or warnings):
                if settings.FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE:
                    # Convert the ignore input from hidden to Checkbox so the
                    # user can change it:
                    self.fields['seen_tidy_warnings'].widget =\
                        forms.CheckboxInput()

                if errors or not (
                        settings.FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE
                        and cleaned_data['seen_tidy_warnings']):
                    self._errors["text"] = self.error_class([mark_safe(
                        _(
                            "HTML validation produced %(count)d warnings."
                            " Please review the updated content below before"
                            " continuing: %(messages)s"
                        ) % {
                            "count": len(warnings) + len(errors),
                            "messages": '<ul><li>%s</li></ul>' % (
                                "</li><li>".join(
                                    map(escape, errors + warnings))),
                        }
                    )])

                # If we're allowed to ignore warnings and we don't have any
                # errors we'll set our hidden form field to allow the user to
                # ignore warnings on the next submit:
                if (not errors
                        and settings.FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE):
                    self.data["%s-seen_tidy_warnings" % self.prefix] = True

        return cleaned_data


class RichTextContent(models.Model):
    """
    Rich text content. Uses TinyMCE by default, but can be configured to do
    anything you want using ``FEINCMS_RICHTEXT_INIT_CONTEXT`` and
    ``FEINCMS_RICHTEXT_INIT_TEMPLATE``.

    If you are using TinyMCE 4.x then ``FEINCMS_RICHTEXT_INIT_TEMPLATE``
    needs to be set to ``admin/content/richtext/init_tinymce4.html``.

    Optionally runs the HTML code through HTML cleaners if you specify
    ``cleanse=True`` when calling ``create_content_type``.
    """

    form = RichTextContentAdminForm
    feincms_item_editor_form = RichTextContentAdminForm

    feincms_item_editor_context_processors = (
        lambda x: settings.FEINCMS_RICHTEXT_INIT_CONTEXT,
    )
    feincms_item_editor_includes = {
        'head': [settings.FEINCMS_RICHTEXT_INIT_TEMPLATE],
    }

    text = RichTextField(_('text'), blank=True)

    class Meta:
        abstract = True
        verbose_name = _('rich text')
        verbose_name_plural = _('rich texts')

    def render(self, **kwargs):
        return render_to_string(
            'content/richtext/default.html',
            {'content': self},
            context_instance=kwargs.get('context'))

    def save(self, *args, **kwargs):
        # TODO: Move this to the form?
        if getattr(self, 'cleanse', None):
            # Passes the rich text content as first argument because
            # the passed callable has been converted into a bound method
            self.text = self.cleanse(self.text)

        super(RichTextContent, self).save(*args, **kwargs)
    save.alters_data = True

    @classmethod
    def initialize_type(cls, cleanse=None):
        def to_instance_method(func):
            def func_im(self, *args, **kwargs):
                return func(*args, **kwargs)
            return func_im

        if cleanse:
            cls.cleanse = to_instance_method(cleanse)

        # TODO: Move this into somewhere more generic:
        if settings.FEINCMS_TIDY_HTML:
            # Make sure we can load the tidy function without dependency
            # failures:
            try:
                get_object(settings.FEINCMS_TIDY_FUNCTION)
            except ImportError as e:
                raise ImproperlyConfigured(
                    "FEINCMS_TIDY_HTML is enabled but the HTML tidy function"
                    " %s could not be imported: %s" % (
                        settings.FEINCMS_TIDY_FUNCTION, e))
