.. _page-ext-navigation:

How can I let 3rd-party apps extend the navigation?
===================================================

Short answer: You need the ``navigation`` extension module. Activate it like
this:

::

    Page.register_extensions('navigation')


Please note however, that this call needs to come after all
``NavigationExtension`` subclasses have been processed, because otherwise they
will not be available for selection in the page administration! (Yes, this is
lame and yes, this is going to change as soon as I find the time to whip up a
better solution.)

Because the use cases for extended navigations are so different, FeinCMS
does not go to great lengths trying to cover them all. What it does though
is to let you execute code to filter, replace or add navigation entries when
generating a list of navigation entries.

If you have a blog and you want to display the blog categories as subnavigation
entries, you could do it as follows:

#. Create a navigation extension for the blog categories

#. Assign this navigation extension to the CMS page where you want these navigation entries to appear

You don't need to do anything else as long as you use the built-in
``feincms_navigation`` template tag -- it knows how to handle extended navigations.

::

    from feincms.module.page.extensions.navigation import NavigationExtension, PagePretender

    class BlogCategoriesNavigationExtension(NavigationExtension):
        name = _('blog categories')

        def children(self, page, **kwargs):
            for category in Category.objects.all():
                yield PagePretender(
                    title=category.name,
                    url=category.get_absolute_url(),
                    )

    class PassthroughExtension(NavigationExtension):
        name = 'passthrough extension'

        def children(self, page, **kwargs):
            for p in page.children.in_navigation():
                yield p

    Page.register_extensions('navigation')
