"""
Simple contact form for FeinCMS. The default form class has name, email, subject
and content fields, content being the only one which is not required. You can
provide your own comment form by passing an additional ``form=YourClass``
argument to the ``create_content_type`` call.
"""

from django import forms
from django.core.mail import send_mail
from django.db import models
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(label=_('name'))
    email = forms.EmailField(label=_('email'))
    subject = forms.CharField(label=_('subject'))

    content = forms.CharField(widget=forms.Textarea, required=False,
        label=_('content'))


class ContactFormContent(models.Model):
    form = ContactForm

    email = models.EmailField()
    subject = models.CharField(max_length=200)

    class Meta:
        abstract = True
        verbose_name = _('contact form')
        verbose_name_plural = _('contact forms')

    @classmethod
    def initialize_type(cls, form=None):
        if form:
            cls.form = form

    def get_template_names(self):
        return 'content/contactform/form.html'

    def get_thanks_template_names(self):
        return 'content/contactform/thanks.html'

    def get_email_template_names(self):
        return 'content/contactform/email.txt'

    def get_form_class(self):
        return self.form

    def process(self, request, **kwargs):
        form_class = self.get_form_class()

        if request.GET.get('_cf_thanks'):
            self.rendered_output = render_to_string(self.get_thanks_template_names(),
                context_instance=RequestContext(request))
            return

        if request.method == 'POST':
            form = form_class(request.POST)

            if form.is_valid():
                send_mail(
                    form.cleaned_data['subject'] or self.subject,
                    render_to_string(self.get_email_template_names(), {
                        'data': form.cleaned_data,
                        }),
                    form.cleaned_data['email'],
                    [self.email],
                    fail_silently=True)

                return HttpResponseRedirect('?_cf_thanks=1')
        else:
            initial = {'subject': self.subject}
            if request.user.is_authenticated():
                initial['email'] = request.user.email
                initial['name'] = request.user.get_full_name()

            form = form_class(initial=initial)

        self.rendered_output = render_to_string(self.get_template_names(), {
            'content': self,
            'form': form,
            }, context_instance=RequestContext(request))

    def render(self, **kwargs):
        return getattr(self, 'rendered_output', u'')
