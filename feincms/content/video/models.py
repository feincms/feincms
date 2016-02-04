from __future__ import absolute_import, unicode_literals

import re

from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


class VideoContent(models.Model):
    """
    Copy-paste a URL to youtube or vimeo into the text box, this content type
    will automatically generate the necessary embed code.

    Other portals aren't supported currently, but would be easy to add if
    anyone would take up the baton.

    You should probably use feincms-oembed.
    """

    PORTALS = (
        ('youtube', re.compile(r'youtube'), lambda url: {
            'v': re.search(r'([?&]v=|./././)([^#&]+)', url).group(2),
        }),
        ('vimeo', re.compile(r'vimeo'), lambda url: {
            'id': re.search(r'/(\d+)', url).group(1),
        }),
        ('sf', re.compile(r'sf\.tv'), lambda url: {
            'id': re.search(r'/([a-z0-9\-]+)', url).group(1),
        }),
    )

    video = models.URLField(
        _('video link'),
        help_text=_(
            'This should be a link to a youtube or vimeo video,'
            ' i.e.: http://www.youtube.com/watch?v=zmj1rpzDRZ0'))

    class Meta:
        abstract = True
        verbose_name = _('video')
        verbose_name_plural = _('videos')

    def get_context_dict(self):
        "Extend this if you need more variables passed to template"
        return {'content': self, 'portal': 'unknown'}

    def get_templates(self, portal='unknown'):
        "Extend/override this if you want to modify the templates used"
        return [
            'content/video/%s.html' % portal,
            'content/video/unknown.html',
        ]

    def ctx_for_video(self, vurl):
        "Get a context dict for a given video URL"
        ctx = self.get_context_dict()
        for portal, match, context_fn in self.PORTALS:
            if match.search(vurl):
                try:
                    ctx.update(context_fn(vurl))
                    ctx['portal'] = portal
                    break
                except AttributeError:
                    continue
        return ctx

    def render(self, **kwargs):
        context_instance = kwargs.get('context')
        ctx = self.ctx_for_video(self.video)
        return render_to_string(
            self.get_templates(ctx['portal']),
            ctx,
            context_instance=context_instance)
