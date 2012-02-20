# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from django.db.models import AutoField
from django.utils.importlib import import_module

# ------------------------------------------------------------------------
def get_object(path, fail_silently=False):
    # Return early if path isn't a string (might already be an callable or
    # a class or whatever)
    if not isinstance(path, (str, unicode)):
        return path

    try:
        dot = path.rindex('.')
        mod, fn = path[:dot], path[dot+1:]
    except ValueError:
        mod, fn = callback, ''

    try:
        return getattr(import_module(mod), fn)
    except (AttributeError, ImportError):
        if not fail_silently:
            raise

# ------------------------------------------------------------------------
def collect_dict_values(data):
    dic = {}
    for key, value in data:
        dic.setdefault(key, []).append(value)
    return dic

# ------------------------------------------------------------------------
def copy_model_instance(obj, exclude=None):
    """
    Copy a model instance, excluding primary key and optionally a list
    of specified fields.
    """

    exclude = exclude or ()
    initial = dict([(f.name, getattr(obj, f.name))
                    for f in obj._meta.fields
                    if not isinstance(f, AutoField) and \
                       not f.name in exclude and \
                       not f in obj._meta.parents.values()])
    return obj.__class__(**initial)

# ------------------------------------------------------------------------
def shorten_string(str, max_length=50):
    """
    Shorten a string for display, truncate it intelligently when too long.
    Try to cut it in 2/3 + ellipsis + 1/3 of the original title. The first part
    also try to cut at white space instead of in mid-word.
    """

    if len(str) >= max_length:
        first_part = int(max_length * 0.6)
        next_space = str[first_part:(max_length / 2 - first_part)].find(' ')
        if next_space >= 0:
            first_part += next_space
        return str[:first_part] + u' … ' + str[-(max_length - first_part):]
    return str

# ------------------------------------------------------------------------
