.. _tools-utils:

:mod:`feincms.utils` --- General utilities
==========================================

.. module:: feincms.utils

.. function:: get_object(path, [fail_silently])

   Helper function which can be used to import a python object. ``path``
   should be the absolute dotted path to the object. You can optionally pass
   ``fail_silently=True`` if the function should not raise an ``Exception``
   in case of a failure to import the object::

       MyClass = get_object('module.MyClass')

       myfunc = get_object('anothermodule.module2.my_function', fail_silently=True)

.. function:: collect_dict_values(data)

   Converts a list of 2-tuples to a dict.

