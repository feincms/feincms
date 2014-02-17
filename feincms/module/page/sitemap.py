# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from django.db.models import Max
from django.db.models import get_model
from django.contrib.sitemaps import Sitemap

from feincms import settings


# ------------------------------------------------------------------------
class PageSitemap(Sitemap):
    """
    The PageSitemap can be used to automatically generate sitemap.xml files
    for submission to index engines. See http://www.sitemaps.org/ for details.
    """
    def __init__(self, navigation_only=False, max_depth=0, changefreq=None,
                 queryset=None, filter=None, extended_navigation=False,
                 page_model=settings.FEINCMS_DEFAULT_PAGE_MODEL,
                 *args, **kwargs):
        """
        The PageSitemap accepts the following parameters for customisation
        of the resulting sitemap.xml output:

        * navigation_only -- if set to True, only pages that are in_navigation
        will appear in the site map.
        * max_depth -- if set to a non-negative integer, will limit the sitemap
        generated to this page hierarchy depth.
        * changefreq -- should be a string or callable specifiying the page
        update frequency, according to the sitemap protocol.
        * queryset -- pass in a query set to restrict the Pages to include
        in the site map.
        * filter -- pass in a callable that transforms a queryset to filter
        out the pages you want to include in the site map.
        * extended_navigation -- if set to True, adds pages from any navigation
        extensions. If using PagePretender, make sure to include title, url,
        level, in_navigation and optionally modification_date.
        """
        super(PageSitemap, self).__init__(*args, **kwargs)
        self.depth_cutoff = max_depth
        self.navigation_only = navigation_only
        self.changefreq = changefreq
        self.filter = filter
        self.extended_navigation = extended_navigation
        if queryset is not None:
            self.queryset = queryset
        else:
            Page = get_model(*page_model.split('.'))
            self.queryset = Page.objects.active()

    def items(self):
        """
        Consider all pages that are active and that are not a redirect
        """

        base_qs = self.queryset
        if callable(base_qs):
            base_qs = base_qs()

        self.max_depth = base_qs.aggregate(Max('level'))['level__max'] or 0
        if self.depth_cutoff > 0:
            self.max_depth = min(self.depth_cutoff, self.max_depth)

        qs = base_qs.filter(redirect_to="")
        if self.filter:
            qs = self.filter(qs)
        if self.navigation_only:
            qs = qs.filter(in_navigation=True)
        if self.depth_cutoff > 0:
            qs = qs.filter(level__lte=self.max_depth - 1)

        pages = [p for p in qs if p.is_active()]

        if self.extended_navigation:
            for idx, page in enumerate(pages):
                if self.depth_cutoff > 0 and page.level == self.max_depth:
                    continue
                if getattr(page, 'navigation_extension', None):
                    cnt = 0
                    for p in page.extended_navigation():
                        depth_too_deep = (
                            self.depth_cutoff > 0
                            and p.level > self.depth_cutoff)
                        not_in_nav = (
                            self.navigation_only
                            and not p.in_navigation)
                        if depth_too_deep or not_in_nav:
                            continue
                        cnt += 1
                        pages.insert(idx + cnt, p)
                        if p.level > self.max_depth:
                            self.max_depth = p.level

        self.per_level = 1.0 / (self.max_depth + 1.0)
        return pages

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
        if getattr(obj, 'override_url', '') == '/':
            prio = 1.0
        else:
            prio = 1.0 - (obj.level + 1) * self.per_level

        # If the page is in_navigation, then it's more important, so boost
        # its importance
        if obj.in_navigation:
            prio += 1.2 * self.per_level

        return "%0.2g" % min(1.0, prio)

# ------------------------------------------------------------------------
