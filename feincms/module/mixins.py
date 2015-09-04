from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

from django.http import Http404
from django.template import Template
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.generic.base import TemplateResponseMixin

from feincms import settings
from feincms.apps import standalone


class ContentModelMixin(object):
    """
    Mixin for ``feincms.models.Base`` subclasses which need need some degree of
    additional control over the request-response cycle.
    """

    #: Collection of request processors
    request_processors = None

    #: Collection of response processors
    response_processors = None

    @classmethod
    def register_request_processor(cls, fn, key=None):
        """
        Registers the passed callable as request processor. A request processor
        always receives two arguments, the current object and the request.
        """
        if cls.request_processors is None:
            cls.request_processors = OrderedDict()
        cls.request_processors[fn if key is None else key] = fn

    @classmethod
    def register_response_processor(cls, fn, key=None):
        """
        Registers the passed callable as response processor. A response
        processor always receives three arguments, the current object, the
        request and the response.
        """
        if cls.response_processors is None:
            cls.response_processors = OrderedDict()
        cls.response_processors[fn if key is None else key] = fn

    # TODO Implement admin_urlname templatetag protocol
    @property
    def app_label(self):
        """
        Implement the admin_urlname templatetag protocol, so one can easily
        generate an admin link using ::

            {% url page|admin_urlname:'change' page.id %}
        """
        return self._meta.app_label

    @property
    def model_name(self):
        "See app_label"
        return self.__class__.__name__.lower()


class ContentObjectMixin(TemplateResponseMixin):
    """
    Mixin for Django's class based views which knows how to handle
    ``ContentModelMixin`` detail pages.

    This is a mixture of Django's ``SingleObjectMixin`` and
    ``TemplateResponseMixin`` conceptually to support FeinCMS'
    ``ApplicationContent`` inheritance. It does not inherit
    ``SingleObjectMixin`` however, because that would set a
    precedence for the way how detail objects are determined
    (and would f.e. make the page and blog module implementation
    harder).
    """

    context_object_name = None

    def handler(self, request, *args, **kwargs):
        if not hasattr(self.request, '_feincms_extra_context'):
            self.request._feincms_extra_context = {}

        r = self.run_request_processors()
        if r:
            return r

        r = self.process_content_types()
        if r:
            return r

        response = self.render_to_response(self.get_context_data())

        r = self.finalize_content_types(response)
        if r:
            return r

        r = self.run_response_processors(response)
        if r:
            return r

        return response

    def get_template_names(self):
        # According to the documentation this method is supposed to return
        # a list. However, we can also return a Template instance...
        if isinstance(self.template_name, (Template, list, tuple)):
            return self.template_name

        if self.template_name:
            return [self.template_name]

        self.object._needs_templates()
        if self.object.template.path:
            return [self.object.template.path]

        # Hopefully someone else has a usable get_template_names()
        # implementation...
        return super(ContentObjectMixin, self).get_template_names()

    def get_context_data(self, **kwargs):
        context = self.request._feincms_extra_context
        context[self.context_object_name or 'feincms_object'] = self.object
        context.update(kwargs)
        return super(ContentObjectMixin, self).get_context_data(**context)

    @property
    def __name__(self):
        """
        Dummy property to make this handler behave like a normal function.
        This property is used by django-debug-toolbar
        """
        return self.__class__.__name__

    def run_request_processors(self):
        """
        Before rendering an object, run all registered request processors. A
        request processor may peruse and modify the page or the request. It can
        also return a ``HttpResponse`` for shortcutting the rendering and
        returning that response immediately to the client.
        """
        if not getattr(self.object, 'request_processors', None):
            return

        for fn in reversed(list(self.object.request_processors.values())):
            r = fn(self.object, self.request)
            if r:
                return r

    def run_response_processors(self, response):
        """
        After rendering an object to a response, the registered response
        processors are called to modify the response, eg. for setting cache or
        expiration headers, keeping statistics, etc.
        """
        if not getattr(self.object, 'response_processors', None):
            return

        for fn in self.object.response_processors.values():
            r = fn(self.object, self.request, response)
            if r:
                return r

    def process_content_types(self):
        """
        Run the ``process`` method of all content types sporting one
        """
        # store eventual Http404 exceptions for re-raising,
        # if no content type wants to handle the current self.request
        http404 = None
        # did any content type successfully end processing?
        successful = False

        for content in self.object.content.all_of_type(tuple(
                self.object._feincms_content_types_with_process)):

            try:
                r = content.process(self.request, view=self)
                if r in (True, False):
                    successful = r
                elif r:
                    return r
            except Http404 as e:
                http404 = e

        if not successful:
            if http404:
                # re-raise stored Http404 exception
                raise http404

            extra_context = self.request._feincms_extra_context

            if (not settings.FEINCMS_ALLOW_EXTRA_PATH and
                    extra_context.get('extra_path', '/') != '/' and
                    # XXX Already inside application content.  I'm not sure
                    # whether this fix is really correct...
                    not extra_context.get('app_config')):
                raise Http404(str('Not found (extra_path %r on %r)') % (
                    extra_context.get('extra_path', '/'),
                    self.object,
                ))

    def finalize_content_types(self, response):
        """
        Runs finalize() on content types having such a method, adds headers and
        returns the final response.
        """

        for content in self.object.content.all_of_type(tuple(
                self.object._feincms_content_types_with_finalize)):

            r = content.finalize(self.request, response)
            if r:
                return r


class ContentView(ContentObjectMixin, generic.DetailView):
    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() not in self.http_method_names:
            return self.http_method_not_allowed(request, *args, **kwargs)
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.object = self.get_object()
        return self.handler(request, *args, **kwargs)


class StandaloneView(generic.View):
    @method_decorator(standalone)
    def dispatch(self, request, *args, **kwargs):
        return super(StandaloneView, self).dispatch(request, *args, **kwargs)
