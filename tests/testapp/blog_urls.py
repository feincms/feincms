from django.conf.urls import patterns, include, url
from django.views import generic

from feincms.module.blog.models import Entry


urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/', generic.DetailView.as_view(
        queryset=Entry.objects.all(),
        ), name='blog_entry_details'),
    url(r'^$', generic.ListView.as_view(
        queryset=Entry.objects.all(),
        ), name='blog_entry_list'),
)
