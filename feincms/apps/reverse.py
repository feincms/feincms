from __future__ import absolute_import, unicode_literals

from functools import wraps

from django.core.cache import cache
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.functional import lazy


APP_REVERSE_CACHE_TIMEOUT = 3


def app_reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
                *vargs, **vkwargs):
    """
    Reverse URLs from application contents

    Works almost like Django's own reverse() method except that it resolves
    URLs from application contents. The second argument, ``urlconf``, has to
    correspond to the URLconf parameter passed in the ``APPLICATIONS`` list
    to ``Page.create_content_type``::

        app_reverse('mymodel-detail', 'myapp.urls', args=...)

        or

        app_reverse('mymodel-detail', 'myapp.urls', kwargs=...)

    The second argument may also be a request object if you want to reverse
    an URL belonging to the current application content.
    """

    # First parameter might be a request instead of an urlconf path, so
    # we'll try to be helpful and extract the current urlconf from it
    extra_context = getattr(urlconf, '_feincms_extra_context', {})
    appconfig = extra_context.get('app_config', {})
    urlconf = appconfig.get('urlconf_path', urlconf)

    from .contents import ApplicationContent
    appcontent_class = ApplicationContent._feincms_content_models[0]
    cache_key = appcontent_class.app_reverse_cache_key(urlconf)
    url_prefix = cache.get(cache_key)

    if url_prefix is None:
        content = appcontent_class.closest_match(urlconf)

        if content is not None:
            if urlconf in appcontent_class.ALL_APPS_CONFIG:
                # We have an overridden URLconf
                app_config = appcontent_class.ALL_APPS_CONFIG[urlconf]
                urlconf = app_config['config'].get('urls', urlconf)

            prefix = content.parent.get_absolute_url()
            prefix += '/' if prefix[-1] != '/' else ''

            url_prefix = (urlconf, prefix)
            cache.set(cache_key, url_prefix, timeout=APP_REVERSE_CACHE_TIMEOUT)

    if url_prefix:
        # vargs and vkwargs are used to send through additional parameters
        # which are uninteresting to us (such as current_app)
        return reverse(
            viewname,
            url_prefix[0],
            args=args,
            kwargs=kwargs,
            prefix=url_prefix[1],
            *vargs, **vkwargs)

    raise NoReverseMatch("Unable to find ApplicationContent for %r" % urlconf)


#: Lazy version of ``app_reverse``
app_reverse_lazy = lazy(app_reverse, str)


def permalink(func):
    """
    Decorator that calls app_reverse()

    Use this instead of standard django.db.models.permalink if you want to
    integrate the model through ApplicationContent. The wrapped function
    must return 4 instead of 3 arguments::

        class MyModel(models.Model):
            @appmodels.permalink
            def get_absolute_url(self):
                return ('myapp.urls', 'model_detail', (), {'slug': self.slug})
    """
    def inner(*args, **kwargs):
        return app_reverse(*func(*args, **kwargs))
    return wraps(func)(inner)
