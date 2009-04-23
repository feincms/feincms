from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
import re

class VideoContent(models.Model):
    video = models.URLField(_('video link'),help_text=_('This should be a link to a youtube video, i.e.: http://www.youtube.com/watch?v=zmj1rpzDRZ0'))

    class Meta:
        abstract = True
        verbose_name = _('video')
        verbose_name_plural = _('videos')

    def render(self, **kwargs):
        vid = re.search('(?<==)\w+',self.video)
        ret = """
            <div class="videocontent">
            <object width="400" height="330">
            <param name="movie" value="http://www.youtube.com/v/%s&hl=de&fs=1"></param>
                <param name="allowFullScreen" value="true"></param>
                <param name="allowscriptaccess" value="always"></param>
                <embed src="http://www.youtube.com/v/%s&hl=de&fs=1&rel=0" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="400" height="330"></embed>
            </object>
            </div>
            """ % (vid.group(0), vid.group(0))
        return ret
