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
create a content type for a media file as follows::

    from feincms.module.page.models import Page
    from feincms.content.medialibrary.v2 import MediaFileContent

    Page.create_content_type(MediaFileContent, TYPE_CHOICES=(
            ('default', _('default')),
            ('lightbox', _('lightbox')),
            ))


``TYPE_CHOICES`` has nothing to do with file types -- it's about choosing
the presentation type for a certain media file, f.e. whether the media file
should be presented inline, in a lightbox, floated, or simply as a download
link.


Configuration
=============

The location and URL of the media library may be configured either by setting
the appropriate variables in your ``settings.py`` file or in your CMS defining
module.

The file system path for all media library files is defined using Django's
``MEDIA_ROOT`` setting and FeinCMS' ``FEINCMS_MEDIALIBRARY_UPLOAD_TO`` setting
which defaults to ``medialibrary/%Y/%m/``.

These settings can also be changed programmatically using
``MediaFile.reconfigure(upload_to=..., storage=...)``


Rendering media file contents
=============================

A set of recognition functions will be run on the file name to determine the file
type. Using combinations of the name and type, the default render method tries to
find a template for rendering the
:class:`~feincms.content.medialibrary.models.MediaFileContent`.

The default set of pre-defined content types and recognition functions is::

    MediaFileBase.register_filetypes(
            ('image', _('Image'), lambda f: re.compile(r'\.(bmp|jpe?g|jp2|jxr|gif|png|tiff?)$', re.IGNORECASE).search(f)),
            ('video', _('Video'), lambda f: re.compile(r'\.(mov|m[14]v|mp4|avi|mpe?g|qt|ogv|wmv)$', re.IGNORECASE).search(f)),
            ('audio', _('Audio'), lambda f: re.compile(r'\.(au|mp3|m4a|wma|oga|ram|wav)$', re.IGNORECASE).search(f)),
            ('pdf', _('PDF document'), lambda f: f.lower().endswith('.pdf')),
            ('swf', _('Flash'), lambda f: f.lower().endswith('.swf')),
            ('txt', _('Text'), lambda f: f.lower().endswith('.txt')),
            ('rtf', _('Rich Text'), lambda f: f.lower().endswith('.rtf')),
            ('zip', _('Zip archive'), lambda f: f.lower().endswith('.zip')),
            ('doc', _('Microsoft Word'), lambda f: re.compile(r'\.docx?$', re.IGNORECASE).search(f)),
            ('xls', _('Microsoft Excel'), lambda f: re.compile(r'\.xlsx?$', re.IGNORECASE).search(f)),
            ('ppt', _('Microsoft PowerPoint'), lambda f: re.compile(r'\.pptx?$', re.IGNORECASE).search(f)),
            ('other', _('Binary'), lambda f: True), # Must be last
        )

You can add to that set by calling ``MediaFile.register_filetypes()`` with your new
file types similar to the above.

If we've got an example file ``2009/06/foobar.jpg`` and a presentation type of
``inline``, the templates tried to render the media file are the following:

* ``content/mediafile/image_inline.html``
* ``content/mediafile/image.html``
* ``content/mediafile/inline.html``
* ``content/mediafile/default.html``

You are of course free to do with the file what you want inside the template,
for example a thumbnail and a lightbox version of the image file, and put everything
into an element that's floated to the left.


Media file metadata
===================

Sometimes, just storing media files is not enough. You've got captions and
copyrights which you'd like to store alongside the media file. This media
library allows that. The caption may even be translated into different
languages. This is most often not necessary or does not apply to copyrights,
therefore the copyright can only be entered once, not once per language.

The default image template ``content/mediafile/image.html`` demonstrates how
the values of those fields can be retrieved and used.


Using the media library in your own apps and content types
==========================================================

There are a few helpers that allow you to have a nice raw_id selector and
thumbnail preview in your own apps and content types that have a ForeignKey to
:class:`~feincms.module.medialibrary.models.MediaFile`.

To have a thumbnail preview in your ModelAdmin and Inline class::

  from feincms.module.medialibrary.fields import MediaFileForeignKey

  class ImageForProject(models.Model):
      project = models.ForeignKey(Project)
      mediafile = MediaFileForeignKey(MediaFile, related_name='+',
                                    limit_choices_to={'type': 'image'})


For the maginfying-glass select widget in your content type inherit your inline
from FeinCMSInline::

  class MyContentInline(FeinCMSInline):
      raw_id_fields = ('mediafile',)

  class MyContent(models.Model):
      feincms_item_editor_inline = MyContentInline

