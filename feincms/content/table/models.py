from django.db import models
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class TableFormatter(object):
    """
    Table formatter which should convert a structure of nested lists into
    a suitable HTML table representation.
    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __call__(self, data):
        return self.format_table(data)

    def format_table(self, data):
        return u'<table class="table">%s</table>' % u''.join(
            self.format_row(index, row) for index, row in enumerate(data))

    def format_row(self, index, row):
        self.row_index = index
        return u'<tr>%s</tr>' % u''.join(
            self.format_cell(index, cell) for index, cell in enumerate(row))

    def format_cell(self, index, cell):
        return u'<td>%s</td>' % cell


class TitleTableFormatter(TableFormatter):
    """
    TitleTableFormatter(first_row_title=True, first_column_title=True)
    """

    def format_cell(self, index, cell):
        if (not self.row_index and getattr(self, 'first_row_title', True)) or \
                (not index and getattr(self, 'first_column_title', True)):
            return u'<th>%s</th>' % cell
        return u'<td>%s</td>' % cell


class TableContent(models.Model):
    """
    Content to edit and display HTML tables in the CMS.

    The standard rich text editor configuration in FeinCMS does not activate
    the table plugin. This content type can be used to edit and display
    nicely formatted HTML tables. It is easy to specify your own table
    renderers.
    """

    feincms_item_editor_includes = {
        'head': ['admin/content/table/init.html'],
        }

    html = models.TextField('HTML', blank=True, editable=False)

    DEFAULT_TYPES = [
        ('plain', _('plain'), TableFormatter()),
        ('titlerow', _('title row'), TitleTableFormatter(
            first_row_title=True, first_column_title=False)),
        ('titlerowcol', _('title row and column'), TitleTableFormatter(
            first_row_title=True, first_column_title=True)),
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
        # XXX ugly, but otherwise the decoder raises exceptions
        self.data = self.data.replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
        self.html = self.data and self.FORMATTERS[self.type](simplejson.loads(self.data)) or u''

        super(TableContent, self).save(*args, **kwargs)
