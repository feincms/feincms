from django.db import models
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _



def plain_formatter(data):
    return u'<table>%s</table>' % u''.join(
            u'<tr>%s</tr>' % u''.join(
             u'<td>%s</td>' % cell for cell in row
            ) for row in data)


def titlerow_formatter(data):
    html = [u'<table>']
    first = True

    for row in data:
        html.append('<tr>')

        if first:
            html.extend([u'<th scope="col">%s</th>' % cell for cell in row])
            first = False
        else:
            html.extend([u'<td>%s</td>' % cell for cell in row])

        html.append('</tr>')

    html.append(u'</table>')
    return u''.join(html)


def titlerowcol_formatter(data):
    html = [u'<table>']
    first = True

    for row in data:
        html.append('<tr>')

        if first:
            html.extend([u'<th scope="col">%s</th>' % cell for cell in row])
            first = False
        else:
            html.append(u'<th scope="row">%s</th>' % row[0])
            html.extend([u'<td>%s</td>' % cell for cell in row[1:]])

        html.append('</tr>')

    html.append(u'</table>')
    return u''.join(html)


class TableContent(models.Model):
    feincms_item_editor_includes = {
        'head': ['admin/content/table/init.html'],
        }

    html = models.TextField('HTML', blank=True, editable=False)

    DEFAULT_TYPES = [
        ('plain', _('plain'), plain_formatter),
        ('titlerow', _('title row'), titlerow_formatter),
        ('titlerowcol', _('title row and column'), titlerowcol_formatter),
        ]

    class Meta:
        abstract = True
        verbose_name = _('table')
        verbose_name_plural = _('tables')

    @classmethod
    def initialize_type(cls, TYPES=None):
        TYPES = TYPES or cls.DEFAULT_TYPES

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
        self.html = self.data and self.FORMATTERS[self.type](simplejson.loads(self.data)) or u''

        super(TableContent, self).save(*args, **kwargs)
