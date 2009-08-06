# ------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------

def build_page_tree(cls):
    """
    Build an in-memory representation of the page tree, trying to keep
    database accesses down to a minimum. The returned dictionary looks like
    this (as json dump):
    
        {"6": {"children": [7, 8, 10], "parent": null, "descendants": [7, 12, 13, 8, 10]},
         "7": {"children": [12], "parent": 6, "descendants": [12, 13]},
         "8": {"children": [], "parent": 6, "descendants": []},
         ...

    """
    all_nodes = { }
    def add_as_descendant(n, p):
        if not n: return
        all_nodes[n.id]['descendants'].append(p.id)
        add_as_descendant(n.parent, p)

    for p in cls.objects.order_by('tree_id', 'lft'):
        all_nodes[p.id] = { 'children' : [ ], 'descendants' : [ ], 'parent' : p.parent_id }
        if(p.parent_id):
            all_nodes[p.parent_id]['children'].append(p.id)
            add_as_descendant(p.parent, p)

    return all_nodes
