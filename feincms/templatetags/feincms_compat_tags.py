from django import template


register = template.Library()


def csrf_token():
    """Dummy implementation for older versions of Django"""
    # Should be deprecated, Django versions prior to 1.2 aren't supported
    # anymore.
    return u''


try:
    from django.template.defaulttags import csrf_token
except ImportError:
    register.simple_tag(csrf_token)
