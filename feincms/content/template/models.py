import os, re

from django import forms
from django.conf import settings
from django.db import models
from django.template.loader import find_template_loader, render_to_string, get_template
from django.template import Context, VariableNode, TemplateDoesNotExist, TemplateSyntaxError
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import admin
from feincms.contrib.fields import JSONField
from feincms.admin.editor import ItemEditorForm


class Object(object):
    pass

def get_templates():
    seen = set()

    yield ('', '----------')

    for loader in settings.TEMPLATE_LOADERS:
        loader_instance = find_template_loader(loader)
        if not loader_instance:
            continue

        for basepath in loader_instance.get_template_sources('.'):
            path = os.path.join(basepath, 'content', 'template')
            try:
                templates = os.listdir(path)
            except (OSError, IOError):
                continue

            for template in templates:
                if template in seen:
                    continue
                if template[:4] == '.tmp':
                    continue
                seen.add(template)
                yield (template, template)

"""{{ tc.field|default:'Hello World!' }}"""


class TemplateContentAdminForm(ItemEditorForm):    
    filename = forms.ChoiceField(label=_('template'))
    custom_fields = set()
    # http://jathan.com/2009/12/08/dynamically-determining-the-variables-for-a-django-template/
    def get_template_vars(self, template):
        varnodes = template.nodelist.get_nodes_by_type(VariableNode)
        return [x.filter_expression.token for x in varnodes]

    def __init__(self, *args, **kwargs):
        super(TemplateContentAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        self.current = []
        if instance:
            self.current = [k for k in instance.tccontext.keys()]
            token = re.compile(r'^tc\.(.*?)(?:\|.*)?$') # token
            filter = re.compile(r'^tc\..*?\|default\: ?(.*)$') #filter
            try:
                template = get_template('content/template/'+instance.filename)
            except TemplateDoesNotExist:
                self.fields['filename'].choices = sorted(get_templates(), key=lambda p: p[1])
                return
            except TemplateSyntaxError:
                return
            for key in self.get_template_vars(template): # gets all template variables
                try:
                    name = token.split(key)[1]
                except IndexError:
                    name = ""
                if name: 
                    if name in self.current:
                        default = instance.tccontext[name]
                    else:
                        try:
                            default = filter.split(key)[1][1:-1]
                        except IndexError:
                            default = ""
                
                    self.custom_fields.add(name)
                    self.fields[name] = forms.CharField(max_length=255, initial=default, required=False,
                                            widget=forms.TextInput(attrs={'size':'40'}))
            
        self.fields['filename'].choices = sorted(get_templates(), key=lambda p: p[1])
    
    def clean(self, *args, **kwargs):
        cleaned_data = super(TemplateContentAdminForm, self).clean(*args, **kwargs)
        return cleaned_data    
   
   
    def save(self, commit=True, *args, **kwargs):
        # Django ModelForms return the model instance from save. We'll
        # call save with commit=False first to do any necessary work &
        # get the model so we can set .parameters to the values of our
        # custom fields before calling save(commit=True)
        model = super(TemplateContentAdminForm, self).save(commit=False, *args, **kwargs)
        
        tc = {}
        for field in self.custom_fields:
            tc.update({field: self.cleaned_data[field]})
        model.tccontext = tc
        
        if commit:
            model.save(**kwargs)
        
        return model    


class TemplateContent(models.Model):
    feincms_item_editor_form = TemplateContentAdminForm
    
    filename = models.CharField(_('template'), max_length=100,
        choices=())
    tccontext = JSONField(null=True, editable=False)

    class Meta:
        abstract = True
        verbose_name = _('template content')
        verbose_name_plural = _('template contents')
        
    def __unicode___(self):
        return self.filename    

    def render(self, **kwargs):
        request = kwargs.get('request')
        context = kwargs.pop('context', None)
        return render_to_string('content/template/%s' % self.filename, 
            {'content': self, 'tc': dict((k, mark_safe(v)) for k, v in self.tccontext.items()),},
              context_instance=context) 

