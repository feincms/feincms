from django.db import models
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


def plain_formatter(data):
    if not data:
        return u''

    data = simplejson.loads(data)

    return u'<table>%s</table>' % u''.join(
            u'<tr>%s</tr>' % u''.join(
             u'<td>%s</td>' % cell for cell in row
            ) for row in data)


class TableContent(models.Model):
    feincms_item_editor_includes = {
        'head': ['admin/content/table/init.html'],
        }

    html = models.TextField('HTML', blank=True, editable=False)

    class Meta:
        abstract = True
        verbose_name = _('table')
        verbose_name_plural = _('tables')

    @classmethod
    def initialize_type(cls, TYPES=None):
        TYPES = TYPES or (('plain', _('plain'), plain_formatter),)

        cls.FORMATTERS = dict((t[0], t[2]) for t in TYPES)
        cls.TYPE_CHOICES = [(t[0], t[1]) for t in TYPES]

        cls.add_to_class('type', models.CharField(_('type'), max_length=20,
            choices=cls.TYPE_CHOICES,
            default=cls.TYPE_CHOICES[0][0]))

        # Add after type, so that type comes before data in admin interface
        cls.add_to_class('data', models.TextField(_('data'), blank=True))

    def render(self, **kwargs):
        return mark_safe(self.html)

    def save(self, *args, **kwargs):
        self.html = self.FORMATTERS[self.type](self.data)

        super(TableContent, self).save(*args, **kwargs)
