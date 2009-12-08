/* All things javascript specific for the classic page change list */

/* 25b6: black right-pointing triangle, 25bc: black down-pointing triangle,
   25b7: white right-pointing triangle, 25BD: white down-pointing triangle */
var expand_sym = '\u25B7';
var collapse_sym = '\u25BD';

var feincms_page_open_list;

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
    var p = page(item_id)
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
    var p = page(item_id)

    if(!p.id || !p.children || p.children.length == 0)
        return false;

    p.ptr.html(expand_sym);
    $.each(p.descendants, function(i, id)
           {
           var pp = page(id);
           if(pp.ptr)
                pp.row.hide()
           });
}

/* Click handler */
var page_tree_handler = function(item_id)
{
    var p = page(item_id);

    if(!p.id || !p.children || p.children.length == 0)
        return false;

    var open = p.open;
    p.open = !open;

    if(open)
        {
        close_subtree(item_id);
        feincms_page_open_list = feincms_page_open_list.filter(function(o) { return o != item_id });
        }
    else
        {
        open_subtree(item_id);
        feincms_page_open_list.push(item_id);
        }

    /* Do I really want that? */
    recolor_lines();

    return false;
}

/* Clean out tree_structure: Remove non existant parents, children, descendants */
var tree_structure_clean = function()
{
    feincms_page_open_list = $.cookie('feincms_page_open_list');

    /* Keep a list of open pages to save state across reloads */
    if(feincms_page_open_list) {
        var lst = feincms_page_open_list.split(',');
        feincms_page_open_list = [];
        for(var i=0; i<lst.length; i++)
            feincms_page_open_list.push(parseInt(lst[i]));
    } else
        feincms_page_open_list = [];

    $(window).unload(function(){
        $.cookie('feincms_page_open_list', feincms_page_open_list.join(','));
    });

    for(k in tree_structure)
        {
            var p = page(k);
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
            var p = page(k);
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
    for(i in feincms_page_open_list)
        {
            var item_id = feincms_page_open_list[i];
            var p = page(item_id);
            // pages could have been deleted
            if(p) p.open = true;
        }
}

var close_entire_tree = function()
{
    for(k in tree_structure)
    {
        close_subtree(k);
    }
    feincms_page_open_list = []
    recolor_lines();
}

var open_entire_tree = function()
{
    feincms_page_open_list = []
    for(k in tree_structure)
    {
        if(page(k) && page(k).children)
        {
            open_subtree(k);
            feincms_page_open_list.push(k);
        }
    }
    recolor_lines();
}

/* Cut/Copy/Paste support */
// FIXME: This changes the site structure and would need to refresh at least the
// tree_structure (if not more, eg. page filter). Easy way out: reload the page.

var cut_item_pk = null;
function cut_item(pk, elem) {
    var row = $(elem.parentNode.parentNode);

    if(row.hasClass('cut')) {
        cut_item_pk = null;
        $('a.paste_target').hide();
        row.removeClass('cut');
    } else {
        cut_item_pk = pk;
        $('a.paste_target').show();
        $('tr').removeClass('cut');
        row.addClass('cut').find('a.paste_target').hide();
    }

    return false;
}

function paste_item(pk, position) {
    if(!cut_item_pk)
        return false;

    $.post('.', {
           '__cmd': 'move_node',
           'position': position,
           'cut_item': cut_item_pk,
           'pasted_on': pk
           }, function(data) {
           if(data == 'OK')
           window.location.reload();
           else
           alert(data);
           });

    return false;
}


