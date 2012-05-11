# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  Created by Vaclav vencax Klecanda on 9.5.2012.
#
# ------------------------------------------------------------------------
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from feincms.admin.item_editor import ItemEditorForm
from django.contrib.admin.widgets import AdminRadioSelect

"""
Embed a poll form anywhere.
"""

from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

# ------------------------------------------------------------------------
class PollContent(models.Model):
    """
    Create a pollquestion content as follows::

        Page.create_content_type(PollContent, TYPE_CHOICES=(
            ('default', _('Default')),
            ('applepie', _('applepie')),
            ('whatever', _('Whatever')),
            ), POLL_CLASS=Poll)

    For a media file of type 'image' and position 'lightbox', the following
    templates are tried in order:

    * content/poll/applepie.html
    * content/poll/default.html

    The context contains ``content`` and ``request`` (if available).
    """
    
    class Meta:
        abstract = True
        verbose_name = _('poll content')
        verbose_name_plural = _('poll contents')

    @classmethod
    def initialize_type(cls, TYPE_CHOICES=None, POLL_CLASS=None):
        if 'feincms.module.medialibrary' not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured, 'You have to add \'feincms.module.medialibrary\' to your INSTALLED_APPS before creating a %s' % cls.__name__

        if POLL_CLASS is None:
            raise ImproperlyConfigured, 'You need to set POLL_CLASS when creating a %s' % cls.__name__
        
        if TYPE_CHOICES is None:
            raise ImproperlyConfigured, 'You need to set TYPE_CHOICES when creating a %s' % cls.__name__

        cls.add_to_class('poll', models.ForeignKey(POLL_CLASS, verbose_name=_('poll object'),
            related_name='%s_%s_set' % (cls._meta.app_label, cls._meta.module_name)
            ))

        cls.add_to_class('polltype', models.CharField(_('polltype'),
            max_length=10, choices=TYPE_CHOICES,
            default=TYPE_CHOICES[0][0],
            help_text=_('Type of poll form to me rendered.')))

        class MediaFileContentAdminForm(ItemEditorForm):
            poll = forms.ModelChoiceField(queryset=POLL_CLASS.objects.all(),
                label=_('poll object'))
            polltype = forms.ChoiceField(choices=TYPE_CHOICES,
                initial=TYPE_CHOICES[0][0], label=_('polltype'),
                widget=AdminRadioSelect(attrs={'class': 'radiolist'}))

        cls.feincms_item_editor_form = MediaFileContentAdminForm

    def render(self, **kwargs):
        request = kwargs.get('request')
        return render_to_string([
            'content/pollquestion/%s.html' % self.polltype,
            'content/pollquestion/default.html',
            ], { 'content': self, 'request': request, 'poll' : self.poll, 
                'items' : self.poll.item_set.all()})

    @classmethod
    def default_create_content_type(cls, cms_model):
        '''
        Convenience method to create default settings.
        '''
        try:
            from poll.models import Poll
        except ImportError:
            raise ImproperlyConfigured('default poll application is django-simple-poll')
        return cms_model.create_content_type(cls, TYPE_CHOICES=(
            ('default', _('Default')),
            ('applepie', _('applepie')),
            ('whatever', _('Whatever')),
        ), POLL_CLASS=Poll)
