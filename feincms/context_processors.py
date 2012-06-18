from feincms.module.page.models import Page


def add_page_if_missing(request):
    """
    If this attribute exists, then a page object has been registered already
    by some other part of the code. We let it decide which page object it
    wants to pass into the template
    """

    try:
        return {
            'feincms_page': Page.objects.for_request(request, best_match=True),
            }
    except Page.DoesNotExist:
        return {}
