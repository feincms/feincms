from feincms.module.page.models import Page


def add_page_if_missing(request):
    """
    Returns ``feincms_page`` for request.
    """

    try:
        return {
            'feincms_page': Page.objects.for_request(request, best_match=True),
        }
    except Page.DoesNotExist:
        return {}
