"""
Simple contact form for FeinCMS. The default form class has name, email,
subject and content fields, content being the only one which is not required.
You can provide your own comment form by passing an additional
``form=YourClass`` argument to the ``create_content_type`` call.
"""

from __future__ import absolute_import, unicode_literals

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

    content = forms.CharField(
        widget=forms.Textarea, required=False,
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

    def process(self, request, **kwargs):
        if request.GET.get('_cf_thanks'):
            self.rendered_output = render_to_string(
                'content/contactform/thanks.html',
                context_instance=RequestContext(request))
            return

        if request.method == 'POST':
            form = self.form(request.POST)

            if form.is_valid():
                send_mail(
                    form.cleaned_data['subject'],
                    render_to_string('content/contactform/email.txt', {
                        'data': form.cleaned_data,
                    }),
                    form.cleaned_data['email'],
                    [self.email],
                    fail_silently=True,
                )

                return HttpResponseRedirect('?_cf_thanks=1')
        else:
            initial = {'subject': self.subject}
            if request.user.is_authenticated():
                initial['email'] = request.user.email
                initial['name'] = request.user.get_full_name()

            form = self.form(initial=initial)

        self.rendered_output = render_to_string(
            'content/contactform/form.html', {
                'content': self,
                'form': form,
            },
            context_instance=RequestContext(request))

    def render(self, **kwargs):
        return getattr(self, 'rendered_output', '')
