from feincms.module.page.models import Page


def add_page_if_missing(request):
    # If this attribute exists, then a page object has been registered already
    # by some other part of the code. We let it decide which page object it
    # wants to pass into the template
    if hasattr(request, '_feincms_page'):
        return {}

    try:
        return {
            'feincms_page': Page.objects.best_match_for_request(request),
            }
    except Page.DoesNotExist:
        return {}

def appcontent_parameters(request):
    """Add ApplicationContent parameters from the request

    ApplicationContent adds the parameters to the request object before
    processing the view so we can expose them to templates here
    """
    if not hasattr(request, '_feincms_appcontent_parameters'):
        return {}
    else:
        return request._feincms_appcontent_parameters
