# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from django.db.models import Max
from django.contrib.sitemaps import Sitemap

from models import Page

# ------------------------------------------------------------------------
class PageSitemap(Sitemap):
    """
    The PageSitemap can be used to automatically generate sitemap.xml files
    for submission to index engines. See http://www.sitemaps.org/ for details.
    """
    def __init__(self, navigation_only=False, max_depth=0, changefreq=None, *args, **kwargs):
        """
        The PageSitemap accepts the following parameters for customisation
        of the resulting sitemap.xml output:

        * navigation_only -- if set to True, only pages that are in_navigation 
        will appear in the site map.
        * max_depth -- if set to a non-negative integer, will limit the sitemap
        generated to this page hierarchy depth.
        * changefreq -- should be a string or callable specifiying the page
        update frequency, according to the sitemap protocol.
        """
        super(PageSitemap, self).__init__(*args, **kwargs)
        self.depth_cutoff    = max_depth
        self.navigation_only = navigation_only
        self.changefreq      = changefreq

    def items(self):
        """
        Consider all pages that are active and that are not a redirect
        """
        self.max_depth = Page.objects.active().aggregate(Max('level'))['level__max']
        if self.depth_cutoff > 0:
            self.max_depth = min(self.depth_cutoff, self.max_depth)

        self.per_level = 1.0 / (self.max_depth + 1.0)

        qs = Page.objects.active().filter(redirect_to="")
        if self.navigation_only:
            qs = qs.filter(in_navigation=True)
        if self.depth_cutoff > 0:
            qs = qs.filter(level__lte=self.max_depth-1)

        return [ p for p in qs if p.is_active() ]

    def lastmod(self, obj):
        return getattr(obj, 'modification_date', None)

    # the priority is computed of the depth in the tree of a page
    # may we should make an extension to give control to the user for priority
    def priority(self, obj):
        """
        The priority is staggered according to the depth of the page in
        the site. Top level get highest priority, then each level is decreased
        by per_level.
        """
        prio = 1.0 - (obj.level + 1) * self.per_level

        # If the page is in_navigation, then it's more important, so boost
        # its importance
        if obj.in_navigation:
            prio += 1.2 * self.per_level

        return "%0.2g" % min(1.0, prio)


    # After a call to the sitemap, be sure to erase the cached _paginator
    # attribute, so next time we'll re-fetch the items list instead of using
    # a stale list.
    def get_urls(self, *args, **kwargs):
        urls = super(PageSitemap, self).get_urls(*args, **kwargs)
        del(self._paginator)
        return urls

# ------------------------------------------------------------------------
