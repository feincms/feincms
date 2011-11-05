from django.http import Http404
from django.template import Template
from django.utils.cache import add_never_cache_headers
from django.views.generic import TemplateView

from feincms import settings
from feincms.module.page.models import Page


class HandlerBase(TemplateView):
    """
    Class-based handler for FeinCMS page content
    """

    def get(self, request, *args, **kwargs):
        return self.handler(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handler(request, *args, **kwargs)

    def handler(self, request, *args, **kwargs):
        self.page = Page.objects.for_request(request, raise404=True, best_match=True, setup=False)
        response = self.prepare()
        if response:
            return response

        response = self.render_to_response(self.get_context_data())
        return self.finalize(response)

    def get_template_names(self):
        # According to the documentation this method is supposed to return
        # a list. However, we can also return a Template instance...
        if isinstance(self.template_name, (Template, list, tuple)):
            return self.template_name

        return [self.template_name or self.page.template.path]

    def get_context_data(self, **kwargs):
        context = self.request._feincms_extra_context
        context['feincms_page'] = self.page
        return context

    def prepare(self):
        """
        Prepare / pre-process content types. If this method returns anything,
        it is treated as a ``HttpResponse`` and handed back to the visitor.
        """

        response = self.page.setup_request(self.request)
        if response:
            return response

        http404 = None     # store eventual Http404 exceptions for re-raising,
                           # if no content type wants to handle the current self.request
        successful = False # did any content type successfully end processing?

        for content in self.page.content.all_of_type(tuple(self.page._feincms_content_types_with_process)):
            try:
                r = content.process(self.request, view=self)
                if r in (True, False):
                    successful = r
                elif r:
                    return r
            except Http404, e:
                http404 = e

        if not successful:
            if http404:
                # re-raise stored Http404 exception
                raise http404

            if not settings.FEINCMS_ALLOW_EXTRA_PATH and \
                    self.request._feincms_extra_context['extra_path'] != '/':
                raise Http404

    def finalize(self, response):
        """
        Runs finalize() on content types having such a method, adds headers and
        returns the final response.
        """

        for content in self.page.content.all_of_type(tuple(self.page._feincms_content_types_with_finalize)):
            r = content.finalize(self.request, response)
            if r:
                return r

        self.page.finalize_response(self.request, response)

        # Add never cache headers in case frontend editing is active
        if hasattr(self.request, "session") and self.request.session.get('frontend_editing', False):
            add_never_cache_headers(response)

        return response

    @property
    def __name__(self):
        """
        Dummy property to make this handler behave like a normal function.
        This property is used by django-debug-toolbar
        """
        return self.__class__.__name__

# ------------------------------------------------------------------------
class Handler(HandlerBase):
    def handler(self, request, *args, **kwargs):
        try:
            return super(Handler, self).handler(request, *args, **kwargs)
        except Http404, e:
            if settings.FEINCMS_CMS_404_PAGE:
                try:
                    request.original_path_info = request.path_info
                    request.path_info = settings.FEINCMS_CMS_404_PAGE
                    response = super(Handler, self).handler(request, *args, **kwargs)
                    response.status_code = 404
                    return response
                except Http404:
                    raise e
            else:
                raise

# ------------------------------------------------------------------------
