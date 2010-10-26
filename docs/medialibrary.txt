.. _medialibrary:

=============
Media library
=============

.. module:: feincms.module.medialibrary

The media library module provides a way to store, transform and display files
of arbitrary types.

The following instructions assume, that you use the media library together
with the page module. However, the media library does not depend on any aspect
of the page module -- you can use it with any CMS base model.

To activate the media library and use it together with the page module, it is
best to first get the page module working with a few content types. Afterwards,
add :mod:`feincms.module.medialibrary` to your ``INSTALLED_APPS`` setting, and
create a content type for a media file as follows:

::

    from feincms.module.page.models import Page
    from feincms.content.medialibrary.models import MediaFileContent

    Page.create_content_type(MediaFileContent, POSITION_CHOICES=(
            ('block', _('block')),
            ('left', _('left')),
            ('right', _('right')),
            ))


The set of positions given here is just an example, you can define the methods
like you want. You should think about positions that make sense for different
media file types, however, because the choice cannot be customized per file
type.


Configuration
=============

The location and URL of the media library may be configured either by setting
the appropriate variables in your ``settings.py`` file or in your CMS defining
module.

The file system path for all media library files is defined using the
``FEINCMS_MEDIALIBRARY_ROOT`` setting (defaults to ``MEDIA_ROOT``). Below that
location, ``FEINCMS_MEDIALIBRARY_UPLOAD_TO`` (defaults to ``medialibrary/%Y/%m/``)
defines the directory to upload individual files to.
The external URL to the media library can be set with ``FEINCMS_MEDIALIBRARY_URL``
(defaults to ``MEDIA_URL``).

These settings can also be defined programmatically using
``MediaFile.reconfigure(upload_to=..., storage=...)``


Rendering media file contents
=============================

A set of recognition functions will be run on the file name to determine the file
type. Using combinations of the name and type, the default render method tries to
find a template for rendering the
:class:`~feincms.content.medialibrary.models.MediaFileContent`.

The default set of pre-defined content types and recognition functions is:

::

    MediaFile.register_filetypes(
            ( 'image', _('Image'),
              lambda f: re.compile(r'\.(jpg|jpeg|gif|png)$', re.IGNORECASE).search(f) ),
            ( 'pdf',   _('PDF document'), lambda f: f.lower().endswith('.pdf') ),
            ( 'txt',   _('Text'),         lambda f: f.lower().endswith('.txt') ),
            ( 'other', _('Binary'),       lambda f: True ), # Must be last
        )

You can add to that set by calling ``MediaFile.register_filetypes()`` with your new
file types similar to the above.

If we've got an example file ``2009/06/foobar.jpg`` and a selected position of
``left``, the templates tried to render the media file are the following:

* ``content/mediafile/image_left.html``
* ``content/mediafile/image.html``
* ``content/mediafile/left.html``
* ``content/mediafile/default.html``

You are of course free to do with the file what you want inside the template,
for example a thumbnail and a lightbox version of the image file, and put everything
into an element that's floated to the left.


Media file metadata
============================

Sometimes, just storing media files is not enough. You've got captions and
copyrights which you'd like to store alongside the media file. This media
library allows that. The caption may even be translated into different
languages. This is most often not necessary or does not apply to copyrights,
therefore the copyright can only be entered once, not once per language.

The default image template ``content/mediafile/image.html`` demonstrates how
the values of those fields can be retrieved and used.
