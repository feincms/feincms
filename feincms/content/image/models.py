from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

class ImageContent(models.Model):
    """
    Create an ImageContent like this:

    Cls.create_content_type(ImageContent, POSITION_CHOICES=(
        ('left', 'Left'),
        ('right', Right'),
        ))
    """

    image = models.ImageField(_('image'), upload_to='imagecontent')

    class Meta:
        abstract = True
        verbose_name = _('image')
        verbose_name_plural = _('images')

    def render(self, **kwargs):
        return render_to_string([
            'content/image/%s.html' % self.position,
            'content/image/default.html',
            ], {'content': self})

    @classmethod
    def handle_kwargs(cls, POSITION_CHOICES=()):
        models.CharField(_('position'), max_length=10, choices=POSITION_CHOICES
            ).contribute_to_class(cls, 'position')

