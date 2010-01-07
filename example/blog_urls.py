from django.conf.urls.defaults import *

from feincms.module.blog.models import Entry

info_dict = {
    'queryset': Entry.objects.all(),
}

urlpatterns = patterns('',
    url(r'^(?P<object_id>\d+)/', 
        'feincms.views.generic.list_detail.object_detail',
        info_dict,
        name = 'blog_entry_details'),
    url(r'^$',
        'feincms.views.generic.list_detail.object_list',
        info_dict,
        name = 'blog_entry_list'),
)