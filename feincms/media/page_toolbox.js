/* All things javascript specific for the classic page change list */

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
    p.ptr.text('-');
    children_ids = p.children;
    $.each(children_ids, function(i, id)
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
    p.ptr.text('+');
    
    children_ids = p.descendants;
    $.each(children_ids, function(i, id)
           {
           pp = page(id);
           if(pp.ptr)
                pp.row.hide()
           });
}

/* Click handler */
var page_tree_handler = function(item_id)
{
    open = page(item_id).open;
    page(item_id).open = !open;
    
    if(open)
        close_subtree(item_id);
    else
        open_subtree(item_id);
    
    /* Do I really want that? */
    recolor_lines();
}

