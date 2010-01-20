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

        # TODO: Check for translation extension before use!
        comment_page = self.parent.original_translation

        f = None
        if self.comments_enabled and request.POST:
            extra = request._feincms_appcontent_parameters.get('page_extra_path', ())
            if len(extra) > 0 and extra[0] == u"post-comment":
                from django.contrib.comments.views.comments import post_comment
                r = post_comment(request)
                if not isinstance(r, HttpResponseRedirect):
                    f = comments.get_form()(comment_page, data=request.POST)

        if f is None:
            f = comments.get_form()(comment_page)

        return render_to_string([
            'content/comments/%s.html' % parent_type,
            'content/comments/default-site.html',
            'content/comments/default.html',
            ], RequestContext(request, { 'content': self, 'feincms_page' : self.parent, 'parent': comment_page, 'form' : f }))

# ------------------------------------------------------------------------



# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
