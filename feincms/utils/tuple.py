"""
Content types in FeinCMS 1.x returned a HTML fragment from ``render()``
methods.

FeinCMS 22.x changed them to return a ``(template_name, context)`` tuple. This
allows rendering content type templates while also having access to all
template variables set in views and context processors without having to
explicitly pass them on or something.

Some old projects still rely on ``render()`` returning a HTML string. This
tuple subclass combines the advantages of both approaches: Newer projects see a
tuple, old projects still get a string.
"""

from django.template.loader import render_to_string


class AutoRenderTuple(tuple):
    def __str__(self):
        return render_to_string(self[0], self[1])
