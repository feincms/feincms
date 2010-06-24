from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson


class JSONFieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, objtype):
        cache_field = '_cached_jsonfield_%s' % self.field
        if not hasattr(obj, cache_field):
            try:
                setattr(obj, cache_field, simplejson.loads(getattr(obj, self.field),
                    parse_float=Decimal))
            except (TypeError, ValueError):
                setattr(obj, cache_field, {})
        return getattr(obj, cache_field)

    def __set__(self, obj, value):
        setattr(obj, '_cached_jsonfield_%s' % self.field, value)
        setattr(obj, self.field, simplejson.dumps(value, cls=DjangoJSONEncoder))