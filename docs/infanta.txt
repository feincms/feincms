===========================
Infanta - FeinCMS extension
===========================

Infanta helps you to easy-integrate and manage reusable apps in FeinCMS

============
INSTALLATION
============

- add 'feincms.thirdparty.infanta' to your INSTALLED_APPS

- add either 
        'django.core.context_processors.request' 
        or
        'feincms.context_processors.add_page_if_missing'
      to your TEMPLATE_CONTEXT_PROCESSORS

-  add the 'feincms.thirdparty.infanta.middleware.InfantaMiddleware' to your MIDDLEWARE_CLASSES

-  add the content type ViewContent

   Page.create_content_type(ViewContent)


Currently it's only fully working if you use the 'feincms.views.base.handler' in your urls for rendering your content.
If you want to change the handler, you have to set the 

from feincms.views.base import handler as feincms_handler

statement in the 'feincms.thirdparty.middleware' to your handler.

=====
HOWTO
=====


For each view of the reusable app you want to be served by the FeinCMS, you have to do the following two steps
(I'm working on ease this step by a command.)

Step 1:
- Create a page for the url of your app's view in the admin and add ViewContent for each block you want to serve (see Step 2)
  e.g.: 
  django-userprofile serves the profile overview under '/accounts/profile/'
  create a page for the url 'accounts/profile' in the admin
  add the content type ViewContent for each block of the rendered template

Step 2:
- In the template which will be rendered by the url's view make sure to
  - remove the '{% extends "base.html" %}' line, as we build the html from FeinCMS
  - load the infanta_tags, which will override the block templatetag
    {% load infanta_tags %}
  - for each block defined in the template, infanta tries to attach the block content to the region defined as first argument
    e.g.:
    {% block main %}
    some content
    {% endblock %}
    the content is attached to the ViewContent defined in the page's region 'main'
   
You can define more than one ViewContent for a region in the admin and more than one block for a region in the template.
Infanta adds them in the ordering of appearance in the template.
   
    



