from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class ImageContent(models.Model):
    BLOCK = 'block'
    LEFT = 'left'
    RIGHT = 'right'

    POSITION_CHOICES = (
        (BLOCK, _('block')),
        (LEFT, _('left')),
        (RIGHT, _('right')),
        )

    CSS_SPEC = {
        BLOCK: 'display:block;',
        LEFT: 'float:left;',
        RIGHT: 'float:right',
        }

    image = models.ImageField(_('image'), upload_to='imagecontent')
    position = models.CharField(max_length=10, choices=POSITION_CHOICES, default=BLOCK)

    class Meta:
        abstract = True

    def render(self, **kwargs):
        return mark_safe(u'<img src="%s" alt="" style="%s" />' % (
            self.image.url,
            self.CSS_SPEC[self.position]))

