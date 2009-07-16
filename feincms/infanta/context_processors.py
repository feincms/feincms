from django.core.exceptions import ImproperlyConfigured

from feincms.module.page.models import Page

def add_page_and_template(request):
    # If this attribute exists, the a page object has been registered already
    # by some other part of the code. We let it decide, which page object it
    # wants to pass into the template
    if hasattr(request, '_feincms_page'):
        return {
            'feincms_page': request._feincms_page,
            'base_template': request._feincms_page.template.path,
            }
    return {}