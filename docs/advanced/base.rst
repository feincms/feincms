.. _tools-base:


:class:`feincms.models.Base` --- CMS base class
===============================================

This is the base class which you must inherit if you'd like to use the CMS to
manage content with the :class:`~feincms.admin.item_editor.ItemEditor`.


.. method:: Base.register_templates(*templates)

.. method:: Base.register_regions(*regions)

.. attribute:: Base.content

   Beware not to name subclass field `content` as this will overshadow `ContentProxy` and you will
   not be able to reference `ContentProxy`. 

.. method:: Base.create_content_type(model, regions=None, [**kwargs])

.. method:: Base.content_type_for(model)

.. method:: Base.copy_content_from(obj)

.. method:: Base.replace_content_with(obj)

.. method:: Base.append_content_from(obj)
