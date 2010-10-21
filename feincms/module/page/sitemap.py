from django.contrib.sitemaps import Sitemap

from models import Page

class PageSitemap(Sitemap): 
    def items(self):
        return Page.objects.filter(active=True, in_navigation=True)
    
    def lastmod(self, obj):
        return obj.modification_date
    
    # the priority is computed of the depth in the tree of a page
    # may we should make an extension to give control to the user for priority
    def priority(self, obj):
        depth = Page.objects.filter(active=True, in_navigation=True).order_by('-level')[0].level

        # This formula means that each level will have its priority
        # reduced by one fifth, so that the fifth level and on will all
        # have a priority of 0.1, with the first level starting at
        # 0.9333... and so on.
        return 1.0 - ((obj.level + 1.0) / (depth + 5.0)) + 0.1

