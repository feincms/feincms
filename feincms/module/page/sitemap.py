

from django.db.models import Max
from django.contrib.sitemaps import Sitemap

from models import Page

class PageSitemap(Sitemap):
    def items(self):
        """
        Consider all pages that are active and that are not a redirect
        """
        self.max_depth = Page.objects.active().aggregate(Max('level'))['level__max']
        self.per_level = 1.0 / (self.max_depth + 1.0)
        return [ p for p in Page.objects.active().filter(redirect_to="") if p.is_active() ]

    def lastmod(self, obj):
        return getattr(obj, 'modification_date', None)

    def changefreq(self, obj):
        return 'daily'

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
