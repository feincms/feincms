.. _advanced-caching:

Performance considerations
==========================

While FeinCMS in its raw form is perfectly capable of serving out a medium
sized site, more complicated setups quickly lead to death by database load.
As the complexity of your pages grows, so do the number of database queries
needed to build page content on each and every request.

It is therefore a good idea to keep an eye open for excessive database queries
and to try to avoid them.


Denormalization
---------------

FeinCMS comes bundled with the "ct_tracker" extension that will reduce the
number of database queries needed by keeping some bookkeeping information
duplicated in the base type.


Caching
-------

Caching rendered page fragments is probably the most efficient way of
reducing database accesses in your FeinCMS site.
An important consideration in the design of your site's templates is which
areas of your pages depend on which variables. FeinCMS supplies a number
of helper methods and variables, ready to be used in your templates.

Here's an (incomplete) list of variables to use in {% cache %} blocks [#djangocache]_:

    * feincms_page.cache_key -- a string describing the current page.
        Depending on the extensions loaded, this varies with the page,
        the page's modification date, its language, etc. This is always
        a safe bet to use on page specific fragments.
        
    * LANGUAGE_CODE -- even if two requests are asking for the same page,
        the html code rendered might differ in translated elements in the
        navigation or elsewhere. If the fragment varies on language, include
        LANGUAGE_CODE in the cache specifier.
        
    * request.user.id -- different users might be allowed to see different
        views of the site. Add request.user.id to the cache specifier if
        this is the case.

.. [#djangocache] Please see the django documentation for detailed 
    description of the {% cache %} template tag.

