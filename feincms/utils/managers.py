# ------------------------------------------------------------------------
class ActiveAwareContentManagerMixin(object):
    """
    Implement what's necessary to add some kind of "active" state for content
    objects. The notion of active is defined by a number of filter rules that
    must all match (AND) for the object to be active.

    A Manager for a content class using the "datepublisher" extension
    should either adopt this mixin or implement a similar interface.
    """

    # A dict of filters which are used to determine whether a page is active or not.
    # Extended for example in the datepublisher extension (date-based publishing and
    # un-publishing of pages)
    active_filters = {}

    @classmethod
    def apply_active_filters(cls, queryset):
        """
        Apply all filters defined to the queryset passed and return the result.
        """
        for filt in cls.active_filters.values():
            if callable(filt):
                queryset = filt(queryset)
            else:
                queryset = queryset.filter(filt)

        return queryset

    @classmethod
    def add_to_active_filters(cls, filter, key=None):
        """
        Add a new clause to the active filters. A filter may be either
        a Q object to be applied to the content class or a callable taking
        a queryset and spitting out a new one.

        If a filter with the given `key` already exists, the new filter
        replaces the old.
        """
        if not cls.active_filters:
            cls.active_filters = {}
        if key is None:
            key = filter
        cls.active_filters[key] = filter

    def active(self):
        """
        Return only currently active objects.
        """
        return self.apply_active_filters(self)
