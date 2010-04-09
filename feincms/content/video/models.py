import re

from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


class VideoContent(models.Model):
    PORTALS = (
        ('youtube', re.compile(r'youtube'), lambda url: {'v': re.search(r'[?&]v=([^#&]+)', url).group(1)}),
        ('vimeo', re.compile(r'vimeo'), lambda url: {'id': re.search(r'/(\d+)', url).group(1)}),
        ('sf', re.compile(r'sf\.tv'), lambda url: {'id': re.search(r'/([a-z0-9\-]+)', url).group(1)}),
        )

    video = models.URLField(_('video link'),
        help_text=_('This should be a link to a youtube or vimeo video, i.e.: http://www.youtube.com/watch?v=zmj1rpzDRZ0'))

    class Meta:
        abstract = True
        verbose_name = _('video')
        verbose_name_plural = _('videos')

    def render(self, **kwargs):
        for portal, match, context_fn in self.PORTALS:
            if match.search(self.video):
                return render_to_string([
                    'content/video/%s.html' % portal,
                    'content/video/unknown.html',
                    ], dict(context_fn(self.video), content=self))

        return render_to_string('content/video/unknown.html', {
            'content': self})
