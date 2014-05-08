# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  Created by Martin J. Laubach on 08.01.10.
#  skyl wuz here (11.05.10)
#
# ------------------------------------------------------------------------

"""
Embed a comment list and comment form anywhere. Uses the standard
``django.contrib.comments`` application.
"""

from __future__ import absolute_import, unicode_literals

from django.contrib import comments
from django.contrib.comments.views.comments import post_comment
from django.db import models
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from feincms.admin.item_editor import ItemEditorForm
from feincms._internal import get_model_name


# ------------------------------------------------------------------------
class CommentsContent(models.Model):
    comments_enabled = models.BooleanField(
        _('enabled'), default=True,
        help_text=_('New comments may be added'))

    class Meta:
        abstract = True
        verbose_name = _('comments')
        verbose_name_plural = _('comments')

    @classmethod
    def initialize_type(cls):
        class CommentContentAdminForm(ItemEditorForm):
            def __init__(self, *args, **kwargs):
                super(CommentContentAdminForm, self).__init__(*args, **kwargs)
                parent = kwargs.get('instance', None)
                if parent is not None:
                    f = self.fields['comments_enabled']
                    r = f.help_text
                    r += '<hr />'
                    comments_model = comments.get_model()
                    for c in comments_model.objects.for_model(
                            parent.parent).order_by('-submit_date'):
                        r += (
                            '<div class="form-row" style="margin-left: 60px">'
                            '# %(pk)d <a href="/admin/%(app)s/%(model)s/%(pk)'
                            'd/">%(comment)s</a> - %(is_public)s</div>') % {
                            'pk': c.id,
                            'comment': c.comment[:80],
                            'is_public': (
                                _('public') if c.is_public
                                else _('not public')),
                            'app': comments_model._meta.app_label,
                            'model': get_model_name(comments_model._meta),
                        }
                    f.help_text = r

        cls.feincms_item_editor_form = CommentContentAdminForm

    def process(self, request, **kwargs):
        parent_type = self.parent.__class__.__name__.lower()

        comment_page = self.parent
        if (hasattr(comment_page, 'original_translation')
                and comment_page.original_translation):
            comment_page = comment_page.original_translation

        f = None
        if self.comments_enabled and request.POST:

            # I guess the drawback is that this page can't handle any other
            # types of posts just the comments for right now, but if we just
            # post to the current path and handle it this way .. at least it
            # works for now.

            # extra = request._feincms_extra_context.get('page_extra_path', ())
            # if len(extra) > 0 and extra[0] == "post-comment":

            r = post_comment(request, next=comment_page.get_absolute_url())

            if isinstance(r, HttpResponseRedirect):
                return r

            f = comments.get_form()(comment_page, data=request.POST)

        if f is None:
            f = comments.get_form()(comment_page)

        self.rendered_output = render_to_string(
            [
                'content/comments/%s.html' % parent_type,
                'content/comments/default-site.html',
                'content/comments/default.html',
            ],
            RequestContext(request, {
                'content': self,
                'feincms_page': self.parent,
                'parent': comment_page,
                'form': f,
            }),
        )

    def render(self, **kwargs):
        return getattr(self, 'rendered_output', '')
