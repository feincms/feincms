Management commands
===================

Database schema checker
-----------------------

.. automodule:: feincms.management.checker
   :members:
   :noindex:


Content-type specific management commands
-----------------------------------------

.. automodule:: feincms.management.commands.update_rsscontent
   :members:
   :noindex:


Page tree rebuilders
--------------------

Those should not normally be used. Older versions of MPTT sometimes
got confused with repeated saves and tree-structure changes. These
management commands helped cleaning up the mess.

.. automodule:: feincms.management.commands.rebuild_mptt
   :members:
   :noindex:


Miscellaneous commands
----------------------

.. automodule:: feincms.management.commands.feincms_validate
   :members:
   :noindex:
