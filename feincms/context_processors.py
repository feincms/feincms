from feincms.module.page.models import Page


def add_page_if_missing(request):
    # If this attribute exists, the a page object has been registered already
    # by some other part of the code. We let it decide, which page object it
    # wants to pass into the template
    if hasattr(request, '_feincms_page'):
        return {}

    return {
        'feincms_page': Page.objects.best_match_for_request(request),
        }
