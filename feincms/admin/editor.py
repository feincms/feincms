import warnings
warnings.warn("Accessing the item and tree editor through `feincms.admin.editor`"
    " has been deprecated. Please use `feincms.admin.item_editor` and"
    " `feincms.admin.tree_editor` instead. `feincms.admin.editor` will be"
    " removed in FeinCMS v1.8.",
    DeprecationWarning, stacklevel=2)

from feincms.admin.item_editor import ItemEditor, ItemEditorForm
from feincms.admin.tree_editor import TreeEditor, ajax_editable_boolean, \
    ajax_editable_boolean_cell, django_boolean_icon
