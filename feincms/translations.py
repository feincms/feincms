"""
This module offers functions and abstract base classes that can be used to
store translated models. There isn't much magic going on here.

Usage example::

    class News(models.Model, TranslatedObjectMixin):
        active = models.BooleanField(default=False)
        created = models.DateTimeField(default=timezone.now)


    class NewsTranslation(Translation(News)):
        title = models.CharField(max_length=200)
        body = models.TextField()


Print the titles of all news entries either in the current language (if
available) or in any other language::

    for news in News.objects.all():
        print(news.translation.title)

Print all the titles of all news entries which have an english translation::

    from django.utils import translation
    translation.activate('en')
    for news in News.objects.filter(translations__language_code='en'):
        print(news.translation.title)
"""

from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils import translation
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from feincms.utils import queryset_transform


class _NoTranslation(object):
    """Simple marker for when no translations exist for a certain object

    Only used for caching."""
    pass


def short_language_code(code=None):
    """
    Extract the short language code from its argument (or return the default
    language code).

    >>> str(short_language_code('de'))
    'de'
    >>> str(short_language_code('de-at'))
    'de'
    >>> short_language_code() == short_language_code(settings.LANGUAGE_CODE)
    True
    """
    if code is None:
        code = translation.get_language()

    pos = code.find('-')
    if pos > -1:
        return code[:pos]
    return code


def is_primary_language(language=None):
    """
    Returns true if current or passed language is the primary language for this
    site.  (The primary language is defined as the first language in
    settings.LANGUAGES.)
    """

    if not language:
        language = translation.get_language()

    return language == settings.LANGUAGES[0][0]


def lookup_translations(language_code=None):
    """
    Pass the return value of this function to .transform() to automatically
    resolve translation objects

    The current language is used if ``language_code`` isn't specified.
    """
    def _transform(qs):
        lang_ = language_code if language_code else translation.get_language()

        instance_dict = {}

        # Don't do anything for those who already have a cached translation
        # available
        for instance in qs:
            trans = cache.get(instance.get_translation_cache_key(lang_))
            if trans:
                if trans is _NoTranslation:
                    instance._cached_translation = None
                else:
                    instance._cached_translation = trans
            else:
                instance_dict[instance.pk] = instance

        # We really, really need something in here to continue
        if not instance_dict:
            return

        candidates = list(
            instance_dict.values()
        )[0].translations.model._default_manager.all()

        if instance_dict:
            _process(candidates, instance_dict, lang_, 'iexact')
        if instance_dict:
            _process(
                candidates,
                instance_dict,
                settings.LANGUAGE_CODE,
                'istartswith',
            )
        if instance_dict:
            for candidate in candidates.filter(
                    parent__pk__in=instance_dict.keys()):
                if candidate.parent_id in instance_dict:
                    _found(instance_dict, candidate)

        # No translations for the rest
        for instance in instance_dict.values():
            instance._cached_translation = None

    def _found(instance_dict, candidate):
        parent = instance_dict[candidate.parent_id]
        cache.set(parent.get_translation_cache_key(), candidate)
        parent._cached_translation = candidate
        candidate.parent = parent
        del instance_dict[candidate.parent_id]

    def _process(candidates, instance_dict, lang_, op_):
        candidates = candidates.filter(
            Q(parent__pk__in=instance_dict.keys()),
            Q(**{'language_code__' + op_: lang_}) |
            Q(**{'language_code__' + op_: short_language_code(lang_)})
        ).order_by('-language_code')

        for candidate in candidates:
            # The candidate's parent might already have a translation by now
            if candidate.parent_id in instance_dict:
                _found(instance_dict, candidate)

    return _transform


class TranslatedObjectManager(queryset_transform.TransformManager):
    """
    This manager offers convenience methods.
    """

    def only_language(self, language=short_language_code):
        """
        Only return objects which have a translation into the given language.

        Uses the currently active language by default.
        """

        return self.filter(translations__language_code=language)


@python_2_unicode_compatible
class TranslatedObjectMixin(object):
    """
    Mixin with helper methods.
    """

    def _get_translation_object(self, queryset, language_code):
        try:
            return queryset.filter(
                Q(language_code__iexact=language_code) |
                Q(language_code__iexact=short_language_code(language_code))
            ).order_by('-language_code')[0]
        except IndexError:
            try:
                return queryset.filter(
                    Q(language_code__istartswith=settings.LANGUAGE_CODE) |
                    Q(language_code__istartswith=short_language_code(
                        settings.LANGUAGE_CODE))
                ).order_by('-language_code')[0]
            except IndexError:
                try:
                    return queryset.all()[0]
                except IndexError:
                    raise queryset.model.DoesNotExist

    def get_translation_cache_key(self, language_code=None):
        """Return the cache key used to cache this object's translations so we
        can purge on-demand"""
        if not language_code:
            language_code = translation.get_language()
        return (
            ('FEINCMS:%d:XLATION:' % getattr(settings, 'SITE_ID', 0)) +
            '-'.join(
                ['%s' % s for s in (
                    self._meta.db_table,
                    self.id,
                    language_code,
                )]
            )
        )

    def get_translation(self, language_code=None):
        if not language_code:
            language_code = translation.get_language()

        key = self.get_translation_cache_key(language_code)

        trans = cache.get(key)

        if trans is None:
            try:
                trans = self._get_translation_object(
                    self.translations.all(), language_code)
            except ObjectDoesNotExist:
                trans = _NoTranslation
            cache.set(key, trans)

        if trans is _NoTranslation:
            return None

        # Assign self to prevent additional database queries
        trans.parent = self
        return trans

    @property
    def translation(self):
        if not hasattr(self, '_cached_translation'):
            self._cached_translation = self.get_translation()
        return self._cached_translation

    @property
    def available_translations(self):
        return self.translations.values_list('language_code', flat=True)

    def __str__(self):
        try:
            translation = self.translation
        except ObjectDoesNotExist:
            return self.__class__.__name__

        if translation:
            return '%s' % translation

        return self.__class__.__name__

    def get_absolute_url(self):
        return self.translation.get_absolute_url()

    def purge_translation_cache(self):
        cache.delete(self.get_translation_cache_key())
        for lang in self.available_translations:
            cache.delete(self.get_translation_cache_key(lang))

        try:
            del self._cached_translation
        except AttributeError:
            pass


def Translation(model):
    """
    Return a class which can be used as inheritance base for translation models
    """

    class Inner(models.Model):
        parent = models.ForeignKey(model, related_name='translations')
        language_code = models.CharField(
            _('language'), max_length=10,
            choices=settings.LANGUAGES, default=settings.LANGUAGES[0][0],
            editable=len(settings.LANGUAGES) > 1)

        class Meta:
            unique_together = ('parent', 'language_code')
            # (beware the above will not be inherited automatically if you
            #  provide a Meta class within your translation subclass)
            abstract = True

        def short_language_code(self):
            return short_language_code(self.language_code)

        def save(self, *args, **kwargs):
            super(Inner, self).save(*args, **kwargs)
            self.parent.purge_translation_cache()
        save.alters_data = True

        def delete(self, *args, **kwargs):
            super(Inner, self).delete(*args, **kwargs)
            self.parent.purge_translation_cache()
        delete.alters_data = True

    return Inner


def admin_translationinline(model, inline_class=admin.StackedInline, **kwargs):
    """
    Returns a new inline type suitable for the Django administration::

        from django.contrib import admin
        from myapp.models import News, NewsTranslation

        admin.site.register(News,
            inlines=[
                admin_translationinline(NewsTranslation),
                ],
            )
    """

    kwargs['extra'] = 1
    kwargs['max_num'] = len(settings.LANGUAGES)
    kwargs['model'] = model
    return type(
        str(model.__class__.__name__ + 'Inline'), (inline_class,), kwargs)
