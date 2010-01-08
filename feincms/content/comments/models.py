# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  Created by Martin J. Laubach on 08.01.10.
#
# ------------------------------------------------------------------------


from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.template import RequestContext

# ------------------------------------------------------------------------
class CommentsContent(models.Model):
    comments_enabled = models.BooleanField(_('enabled'), default=True)

    class Meta:
        abstract = True
        verbose_name = _('comments')
        verbose_name_plural = _('comments')

    def render(self, **kwargs):
        parent_type = self.parent.__class__.__name__.lower()
        request = kwargs.get('request')

        return render_to_string([
            'content/comments/%s.html' % parent_type,
            'content/comments/default-site.html',
            'content/comments/default.html',
            ], RequestContext(request, { 'content': self, 'parent': self.parent }))

# ------------------------------------------------------------------------



# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
