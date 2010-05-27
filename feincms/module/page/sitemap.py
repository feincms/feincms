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
        return 1 - float( float(obj.level + 1) / float(depth + 1)) + 0.01