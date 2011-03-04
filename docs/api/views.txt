Views and decorators
====================


Standard views
--------------

.. automodule:: feincms.views.base
   :members:
   :noindex:


``ApplicationContent``-enabled views
------------------------------------

.. automodule:: feincms.views.applicationcontent
   :members:
   :noindex:


Generic-views replacements
--------------------------

All views in the ``feincms.views.generic`` module are almost the same
as their counterparts in ``django.views.generic`` (before class-based
views came along), except that they add a ``feincms_page`` object to
the context.


.. automodule:: feincms.views.generic.simple
   :members:
   :noindex:

.. automodule:: feincms.views.generic.list_detail
   :members:
   :noindex:

.. automodule:: feincms.views.generic.date_based
   :members:
   :noindex:

.. automodule:: feincms.views.generic.create_update
   :members:
   :noindex:


Decorators
----------

.. automodule:: feincms.views.decorators
   :members:
   :noindex:
