var popup_bg = '<div id="popup_bg"></div>';

function row_node_id(elem) {
    return parseInt(elem.attr('id').substr(4));
}

function row_parent_id(row) {
    return parseInt(row.attr('class').match(/childof(\d+)/)[1]);
}

function row_level(row) {
    return parseInt(row.attr('class').match(/level(\d+)/)[1]);
}

function get_children(row) {
    return $('tr.childof'+row_node_id(row));
}

function get_parent(row) {
    return $('tr#item'+row_parent_id(row));
}

function get_next_sibling(row) {
    // select all siblings of the given row with the purpose of finding
    // the next element on the same level
    var siblings = $('tr.childof'+row_parent_id(row));
    return siblings[siblings.index(row[0])+1];
}

function get_descendants(row) {
    if(!row.hasClass('parent'))
        // return object which will not have any elements
        return $('html>xyz');
    
    var next = get_next_sibling(row);

    // find the global indices of the two rows
    var rows = $('#sitetree tbody tr');
    var global_first = rows.index(row[0]);

    if(typeof(next)=='undefined') {
        // there are two reasons why this might be:
        // 1. all items to the end are descendants of the current node
        // 2. the given node is the last on its level -- there might be
        //    later nodes higher up the tree
        // We have to loop until we either run out of items or until we
        // find such a node, unfortunately.

        var item = $(rows[global_first+1]);
        var level = row_level(row);
        var offset = 1;
        while(item) {
            if(row_level(item)<level) {
                next = item;
                break;
            }

            item = $(rows[global_first+(++offset)]);
        }
    }

    var global_last = next?rows.index(next):0;

    // apply filtering to find all descendants
    if(global_last)
        rows = rows.filter(':lt('+global_last+')');
    return rows.filter(':gt('+global_first+')');
}

function expandall(yesno) {
    if(yesno)
        $('#sitetree tbody tr').show().filter('.parent').addClass('expanded');
    else
        $('#sitetree tbody tr').not('.childof0').hide().end().filter('.parent').removeClass('expanded');

    return false;
}

function drop_item(dragged, target, method) {
    if(dragged[0]==target[0]) {
        return;
    }

    var descendants = get_descendants(dragged);

    // cannot make element a descendant of itself
    if(descendants.index(target[0])!=-1) {
        show_alert(DROP_FAILURE_MESSAGE);
        return;
    }

    var old_level = row_level(dragged);
    var new_level = row_level(target)+(method=='child'?1:0);
    var delta_level = new_level-old_level;
    var apply_delta = function(row){
        if(delta_level) {
            var old = row_level(row);
            row.removeClass('level'+old).addClass('level'+(old+delta_level));
        }};

    var old_parent = row_parent_id(dragged);
    var new_parent = (method=='child'?row_node_id(target):row_parent_id(target));

    // was the dragged element the last child of its former parent?
    var dragged_parent = get_parent(dragged);
    if(dragged_parent.length) {
        // dragged_parent is empty if dragged is/was a toplevel object
        if(old_parent!=new_parent && get_children(dragged_parent).length==1)
            dragged_parent.removeClass('parent');
    }

    if(method=='before') {
        var len = descendants.length;

        if(len) {
            var first_descendant = $(descendants[0]);
            console.log(first_descendant);
            console.log(len);
            var i = 0;
            while(i<len) {
                var row = $(descendants[i++]);
                apply_delta(row);
                target.before(row);
                console.log(row);
            }
            
            for(var i=0; i++; i<len) {
                console.log(i++);
                var row = $(descendants[i]);
                console.log(row);
                apply_delta(row);
                target.before(row);
                console.log(row);
            }
            first_descendant.before(dragged);
        } else
            target.before(dragged);
    } else {
        var insertion_target = target;

        if(target.hasClass('parent')) {
            insertion_target = get_children(target);
            insertion_target = $(insertion_target[insertion_target.length-1]);
        }

        var i = descendants.length;
        while(i-->0) {
            var row = $(descendants[i]);
            apply_delta(row);
            insertion_target.after(row);
        }

        insertion_target.after(dragged);
    }

    dragged.removeClass('childof'+old_parent).addClass('childof'+new_parent);
    dragged.removeClass('level'+old_level).addClass('level'+new_level);

    if(method=='child' && !target.hasClass('expanded')) {
        dragged.hide().removeClass('expanded');
        descendants.hide().removeClass('expanded');
        target.find('td:first-child').removeClass('hover').switchClass('highlight', 'nohighlight');
    } else
        dragged.find('td:first-child').removeClass('hover').switchClass('highlight', 'nohighlight');

    target.find('td:first-child').removeClass('hover');

    // if drag method is 'child', the new target is a parent for sure
    if(method=='child')
        target.addClass('parent');
}


/* dialogs */

function show_alert(message, title) {
    $("body").append(popup_bg);
    jAlert(message, title, function(){
        $("#popup_bg").remove();
    });
}


/* tree editor integration methods */

function delete_item() {
    var row = $(this).parents('tr');

    if(get_children(row).length) {
        show_alert(DELETE_MESSAGES[4], DELETE_MESSAGES[3])

        return false;
    }

    jConfirm(DELETE_MESSAGES[0], DELETE_MESSAGES[1], function(r) {
        if (r==true) {
            $.post('.', {'__cmd': 'delete_item', 'item_id': row_node_id(row)}, function(data){
                if (data == "OK") {
                    var parent = get_parent(row);
                    if(get_children(parent).length==1)
                        parent.removeClass('parent');

                    row.fadeOut().remove();
                    show_alert(DELETE_MESSAGES[2], DELETE_MESSAGES[2]);
                } else {
                    show_alert(data, data);
                }
            });
        }
        $(".popup_bg").remove();
    });
}

function save_item_tree() {
    var tree = [];
    $('#sitetree tbody tr').each(function(){
        var row = $(this);
        tree.push([row_node_id(row), row_parent_id(row), row.hasClass('parent')]);
    });

    $.post('.', {'__cmd': 'save_tree', 'tree': $.toJSON(tree)}, function(data){
        if (data == "OK")
            show_alert(TREE_SAVED_MESSAGE, TREE_SAVED_MESSAGE);
        else
            show_alert(data, data);
    });
}

$(document).ready(function()  {
    // configure expanders
    $('tr.parent div.expander').live('click', function(){
        var row = $(this).parents('tr');
        if(row.hasClass('expanded')) {
            get_descendants(row).hide().removeClass('expanded');
            row.removeClass('expanded');
        } else {
        	get_children(row).show();
            row.addClass('expanded');
        }
    });

    $('#sitetree tbody td:first-child .suchadrag img').draggable({
        appendTo: '#sitetree-wrapper',
        helper: function(){return $(this.parentNode).clone();},
        opacity: 0.8,
        revert: 'invalid',
        scroll: true,
        start: function(){ $('#sitetree td:first-child')
            .removeClass('hover')
            .removeClass('highlight')
            .removeClass('nohighlight'); }
        });

    $('#sitetree tbody td:first-child .suchadrag').droppable({
        over: function(e, ui) { $(this.parentNode).addClass('hover'); },
        out: function(e, ui) { $('#sitetree td:first-child').removeClass('hover'); },
        drop: function(e, ui) {
            var dragged = $(ui.draggable).parents('tr');
            var target = $(this).parents('tr');

            drop_item(dragged, target, ui.draggable[0].className.match(/move-(\w+)/)[1]);

        }
    });
    
    $("input.save_tree").click(save_item_tree);
    $("img.del-page").click(delete_item);

    // initial settings ... everything is collapsed except the first level
    expandall(false);
    $('#sitetree tr.parent.childof0 .expander').trigger('click');
});

function get_expanded_nodes() {
    // Shorter: return $('#sitetree tr.expanded').map(function() { return row_node_id($(this)) })
    
    var nodes = [];
    $('#sitetree tr.expanded').each(function(){
        nodes.push(this.id.substr(4));
    });

    return nodes;
}

function set_expanded_nodes(nodes) {
    expandall(false);
    var i = nodes.length;
    while(i-->0) {
        var row = $('#item'+nodes[i]);
        console.log(row);
        get_children(row).show();
        row.addClass('expanded');
    }
}

function toggle_boolean(elem, attr) {
    var row = $(elem.parentNode.parentNode);

    $.post('.', {
        '__cmd': 'toggle_boolean',
        'item_id': row_node_id(row),
        'attr': attr
        }, function(data) {
            for(var i=0; i<data.length; i++) {
                var elem = $('#item'+data[i][0]+' a.attr_'+attr);
                elem.replaceWith(data[i][1]);
            }
        }, 'json');
    return false;
}
