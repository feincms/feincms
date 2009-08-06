/* All things javascript specific for the classic page change list */

var get_page_row = function(item_id) { return tree_structure[item_id]['row']; }
var get_page_ptr = function(item_id) { return tree_structure[item_id]['ptr']; }
var get_page_children = function(item_id) { return tree_structure[item_id]['children']; }
var get_page_descendants = function(item_id) { return tree_structure[item_id]['descendants']; }

var recolor_lines = function()
{
    $('tbody tr').removeClass('row1').removeClass('row2');
    $('tbody tr:visible:even').addClass('row1');
    $('tbody tr:visible:odd').addClass('row2');
}

/* show all immediate children, then open all children that are marked as open */
var open_subtree = function(item_id)
{
    get_page_ptr(item_id).text('-');
    children_ids = get_page_children(item_id);
    $.each(children_ids, function(i, id)
           {
           if(tree_structure[id]['open'])
           open_subtree(id);
           get_page_row(id).show();
           });
}

/* hide all descendants */
var close_subtree = function(item_id)
{
    get_page_ptr(item_id).text('+');
    
    children_ids = get_page_descendants(item_id);
    $.each(children_ids, function(i, id) { get_page_row(id).hide() });
}

/* Click handler */
var page_tree_handler = function(item_id)
{
    open = tree_structure[item_id]['open'];
    tree_structure[item_id]['open'] = !open;
    
    if(open)
        close_subtree(item_id);
    else
        open_subtree(item_id);
    
    /* Do I really want that? */
    recolor_lines();
}

/* After loading the page, show all root nodes */
$(function()
  {
  for(k in tree_structure)
  {
  /* Precompute object links for no object-id lookups later */
  m = $('#page_marker-' + k);
  tree_structure[k]['ptr'] = m;
  tree_structure[k]['row'] = m.parents('tr:first');
  
  /* Show all root nodes */
  if(tree_structure[k]['parent'] == null)
  tree_structure[k]['row'].show();
  else
  tree_structure[k]['row'].hide();
  }
  
  /* yuck :-) */
  $('table thead tr th:eq(2)').attr('style', 'width: 450px;');
  $('tr td').attr('style', 'text-align: center;');
  
  $('tbody tr').removeClass('row1').removeClass('row2');
  $('table').show();
  recolor_lines();
  });
