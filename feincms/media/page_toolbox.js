/* All things javascript specific for the classic page change list */

/* 25b6: black right-pointing triangle, 25bc: black down-pointing triangle,
   25b7: white right-pointing triangle, 25BD: white down-pointing triangle */
var expand_sym = '\u25B7';
var collapse_sym = '\u25BD';

/* Keep a list of open pages to save state across reloads */
if(sessvars.feincms_page_open_list == null)
    sessvars.feincms_page_open_list = []


var page = function(item_id) { return tree_structure[item_id]; }

var recolor_lines = function()
{
    $('tbody tr').removeClass('row1').removeClass('row2');
    $('tbody tr:visible:even').addClass('row1');
    $('tbody tr:visible:odd').addClass('row2');
}

/* show all immediate children, then open all children that are marked as open */
var open_subtree = function(item_id)
{
    p = page(item_id)
    if(p.children.length == 0)
        return;

    p.ptr.html(collapse_sym);
    $.each(p.children, function(i, id)
           {
           pp = page(id)
           if(pp.ptr)
               {
               pp.row.show();
               if(pp.open)
                    open_subtree(id);
               }
           });
}

/* hide all descendants */
var close_subtree = function(item_id)
{
    p = page(item_id)
    if(p.descendants.length == 0)
        return;
    p.ptr.html(expand_sym);
    $.each(p.descendants, function(i, id)
           {
           pp = page(id);
           if(pp.ptr)
                pp.row.hide()
           });
}

/* Click handler */
var page_tree_handler = function(item_id)
{
    p = page(item_id);
    
    if(p.children.length == 0)
        return;

    open = p.open;
    p.open = !open;
    
    if(open)
        {
        close_subtree(item_id);
        sessvars.feincms_page_open_list = sessvars.feincms_page_open_list.filter(function(o) { return o != item_id });
        }
    else
        {
        open_subtree(item_id);
        sessvars.feincms_page_open_list.push(item_id);
        }

    /* Do I really want that? */
    recolor_lines();
}

/* Clean out tree_structure: Remove non existant parents, children, descendants */
var tree_structure_clean = function()
{
    for(k in tree_structure)
        {
            p = page(k);
            /* Precompute object links for no object-id lookups later */
            m = $('#page_marker-' + k);
            if(m.length)
                {
                    p.ptr = m;
                    p.row = m.parents('tr:first');
                }
            else /* row not present in changelist, throw node away */
                {
                    tree_structure[k] = { }
                }
        }
    
    /* Clean out tree_structure: Remove non existant parents, children, descendants */
    for(k in tree_structure)
        {
            p = page(k);
            if(p.parent && !page(p.parent).ptr)
                p.parent = null
                
                if(p.descendants)
                    p.descendants = $.grep(p.descendants, function(o) { return page(o).ptr; });
            
            if(p.children)
                {
                    p.children = $.grep(p.children, function(o) { return page(o).ptr; });
                    if(p.children.length)
                        p.ptr.html(expand_sym);
                }
        }
    for(i in sessvars.feincms_page_open_list)
        {   
            item_id = sessvars.feincms_page_open_list[i];
            page(item_id).open = true;
        }
}

