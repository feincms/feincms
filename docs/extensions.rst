.. _extensions:

Extensions
==========

The extensions mechanism has been refactored to remove the need to make models
know about their related model admin classes. The new module
:py:mod:`feincms.extensions` contains mixins and base classes - their purpose
is as follows:

.. class:: feincms.extensions.ExtensionsMixin

    This mixin provides the ``register_extensions`` method which is the place
    where extensions are registered for a certain model. Extensions can be
    specified in the following ways:

    - Subclasses of :py:class:`~feincms.extensions.Extension`
    - Dotted Python module paths pointing to a subclass of the aforementioned
      extension class
    - Dotted Python module paths pointing to a module containing either a class
      named ``Extension`` or a function named ``register`` (for legacy
      extensions)


.. class:: feincms.extensions.Extension

    This is the base class for your own extension. It has the following methods
    and properties:

    .. attribute:: model

        The model class.

    .. method:: handle_model(self)

        The method which modifies the Django model class. The model class is
        available as ``self.model``.

    .. method:: handle_modeladmin(self, modeladmin)

        This method receives the model admin instance bound to the model. This
        method could be called more than once, especially when using more than
        one admin site.


.. class:: feincms.extensions.ExtensionModelAdmin()

    This is a model admin subclass which knows about extensions, and lets the
    extensions do their work modifying the model admin instance after it has
    been successfully initialized. It has the following methods and properties:

    .. method:: initialize_extensions(self)

        This method is automatically called at the end of initialization and
        loops through all registered extensions and calls their
        ``handle_modeladmin`` method.

    .. method:: add_extension_options(self, \*f)

        This is a helper to add fields and fieldsets to a model admin instance.
        Usage is as follows::

            modeladmin.add_extension_options('field1', 'field2')

        Or::

            modeladmin.add_extension_options(_('Fieldset title'), {
                'fields': ('field1', 'field2'),
                })


.. note::

  Only model and admin instances which inherit from
  :class:`~feincms.extensions.ExtensionsMixin` and
  :class:`~feincms.extensions.ExtensionModelAdmin` can be extended
  this way.