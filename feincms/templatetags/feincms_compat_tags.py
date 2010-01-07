from django import template


register = template.Library()


def csrf_token():
    """Dummy implementation for older versions of Django"""
    return u''


try:
    from django.template.defaulttags import csrf_token
except ImportError:
    register.simple_tag(csrf_token)
