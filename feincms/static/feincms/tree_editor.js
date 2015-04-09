// Suppress initial rendering of result list, but only if we can show it with
// JS later on.
document.write('<style type="text/css">#result_list { display: none }</style>');

// https://docs.djangoproject.com/en/1.4/ref/contrib/csrf/
feincms.jQuery.ajaxSetup({
    crossDomain: false,  // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type))) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    }
});

feincms.jQuery(function($){
    // recolor tree after expand/collapse
    $.extend($.fn.recolorRows = function() {
        $('tr:visible:even', this).removeClass('row1').addClass('row2');
        $('tr:visible:odd', this).removeClass('row2').addClass('row1');

        /* Mark inactive rows */
        $('tr.item_inactive').removeClass('item_inactive');
        var in_wrap_active = $('div[id^=wrap_active_]');
        var in_wrap_input = $('input', in_wrap_active);
        $(':checkbox:not(:checked)', in_wrap_input).parents('tr').addClass('item_inactive');
        $('img', in_wrap_active).parents('tr').addClass('item_inactive');
    });

    $(document.body).on('click', '[data-inplace]', function() {
        var elem = $(this),
            id = elem.data('inplace-id'),
            attr = elem.data('inplace-attribute');

        $.ajax({
            url: ".",
            type: "POST",
            dataType: "json",
            data: {
                '__cmd': 'toggle_boolean',
                'item_id': id,
                'attr': attr
            },
            success: function(data) {
                $.each(data, function(i, html) {
                    var r_id = $(html).attr('id');
                    $('#' + r_id).replaceWith(html);
                });
                $('#result_list tbody').recolorRows();
            },

            error: function(xhr, status, err) {
                alert("Unable to toggle " + attr + ": " + xhr.responseText);
            }
        });
    });


    /* Extract an object id (numeric) from a DOM id. Assumes that a "-" is used
       as delimiter. Returns either the id found or 0 if something went wrong.

           extractItemId('foo_bar_baz-327') -> 327
     */
    function extractItemId(elem_id) {
        var i = elem_id.indexOf('-');
        if(i >= 0)
            return parseInt(elem_id.slice(i+1), 10);

        return 0;
    }

    function isExpandedNode(id) {
        return feincms.collapsed_nodes.indexOf(id) == -1;
    }

    function markNodeAsExpanded(id) {
        // remove itemId from array of collapsed nodes
        var idx = feincms.collapsed_nodes.indexOf(id);
        if(idx >= 0)
            feincms.collapsed_nodes.splice(idx, 1);
    }

    function markNodeAsCollapsed(id) {
        if(isExpandedNode(id))
            feincms.collapsed_nodes.push(id);
    }

    // toggle children
    function doToggle(id, show) {
        var children = feincms.tree_structure[id];
        for (var i=0; i<children.length; ++i) {
            var childId = children[i];
            if(show) {
                $('#item-' + childId).show();
                // only reveal children if current node is not collapsed
                if(isExpandedNode(childId)) {
                    doToggle(childId, show);
                }
            } else {
                $('#item-' + childId).hide();
                // always recursively hide children
                doToggle(childId, show);
            }
        }
    }

    function rowLevel($row) {
        return parseInt($row.attr('rel').replace(/[^\d]/ig, ''));
    }

    /*
     * FeinCMS Drag-n-drop tree reordering.
     * Based upon code by bright4 for Radiant CMS, rewritten for
     * FeinCMS by Bjorn Post.
     *
     * September 2010
     *
     */
    $.extend($.fn.feinTree = function() {
        $('tr', this).each(function(i, el) {
            // adds 'children' class to all parents
            var pageId = extractItemId($('.page_marker', el).attr('id'));
            $(el).attr('id', 'item-' + pageId);
            if (feincms.tree_structure[pageId].length) {
                    $('.page_marker', el).addClass('children');
            }

            // set 'level' on rel attribute
            var pixels = $('.page_marker', el).css('width').replace(/[^\d]/ig,"");
            var rel = Math.round(pixels/18);
            $(el).attr('rel', rel);
        });

        $('div.drag_handle').bind('mousedown', function(event) {
            var BEFORE = 0;
            var AFTER = 1;
            var CHILD = 2;
            var CHILD_PAD = 20;
            var originalRow = $(event.target).closest('tr');
            var rowHeight = originalRow.height();
            var childEdge = $(event.target).offset().left + $(event.target).width();
            var moveTo = new Object();
            var expandObj = new Object();

            $("body").addClass('dragging').disableSelection().bind('mousemove', function(event) {
                // attach dragged item to mouse
                var cloned = originalRow.html();
                if($('#ghost').length == 0) {
                    $('<div id="ghost"></div>').appendTo('body');
                }
                $('#ghost').html(cloned).css({
                    'opacity': .8,
                    'position': 'absolute',
                    'top': event.pageY,
                    'left': event.pageX-30,
                    'width': 600
                });

                // check on edge of screen
                if(event.pageY+100 > $(window).height()+$(window).scrollTop()) {
                    $('html,body').stop().animate({scrollTop: $(window).scrollTop()+250 }, 500);
                } else if(event.pageY-50 < $(window).scrollTop()) {
                    $('html,body').stop().animate({scrollTop: $(window).scrollTop()-250 }, 500);
                }

                // check if drag_line element already exists, else append
                if($("#drag_line").length < 1) {
                    $("body").append('<div id="drag_line" style="position:absolute">line<div></div></div>');
                }

                // loop trough all rows
                $("tr", originalRow.parent()).each(function(index, element) {
                    var element = $(element),
                        top = element.offset().top;

                    // check if mouse is over a row
                    if (event.pageY >= top && event.pageY < top + rowHeight) {
                        var targetRow = null,
                            targetLoc = null,
                            elementLevel = rowLevel(element);

                        if (event.pageY >= top && event.pageY < top + rowHeight / 3) {
                            targetRow = element;
                            targetLoc = BEFORE;
                        } else if (event.pageY >= top + rowHeight / 3 && event.pageY < top + rowHeight * 2 / 3) {
                            var next = element.next();
                            // there's no point in allowing adding children when there are some already
                            // better move the items to the correct place right away
                            if (!next.length || rowLevel(next) <= elementLevel) {
                                targetRow = element;
                                targetLoc = CHILD;
                            }
                        } else if (event.pageY >= top + rowHeight * 2 / 3 && event.pageY < top + rowHeight) {
                            var next = element.next();
                            if (!next.length || rowLevel(next) <= elementLevel) {
                                targetRow = element;
                                targetLoc = AFTER;
                            }
                        }

                        if(targetRow) {
                            var padding = 37 + element.attr('rel') * CHILD_PAD + (targetLoc == CHILD ? CHILD_PAD : 0 );

                            $("#drag_line").css({
                                'width': targetRow.width() - padding,
                                'left': targetRow.offset().left + padding,
                                'top': targetRow.offset().top + (targetLoc == AFTER || targetLoc == CHILD ? rowHeight: 0) -1
                            });

                                    // Store the found row and options
                            moveTo.hovering = element;
                            moveTo.relativeTo = targetRow;
                            moveTo.side = targetLoc;

                            return true;
                        }
                    }
                });
            });

            $('body').keydown(function(event) {
                if (event.which == '27') {
                    $("#drag_line").remove();
                    $("#ghost").remove();
                    $("body").removeClass('dragging').enableSelection().unbind('mousemove').unbind('mouseup');
                    event.preventDefault();
                }
            });

            $("body").bind('mouseup', function(event) {
                if(moveTo.relativeTo) {
                    var cutItem = extractItemId(originalRow.find('.page_marker').attr('id'));
                    var pastedOn = extractItemId(moveTo.relativeTo.find('.page_marker').attr('id'));
                    // get out early if items are the same
                    if(cutItem != pastedOn) {
                        var isParent = (moveTo.relativeTo.next().attr('rel') > moveTo.relativeTo.attr('rel'));
                        var position = '';

                        // determine position
                        if(moveTo.side == CHILD && !isParent) {
                            position = 'last-child';
                        } else if (moveTo.side == BEFORE) {
                            position = 'left';
                        } else {
                            position = 'right';
                        }

                        // save
                        $.post('.', {
                            '__cmd': 'move_node',
                            'position': position,
                            'cut_item': cutItem,
                            'pasted_on': pastedOn
                        }, function(data) {
                                window.location.reload();
                        });
                    } else {
                        $("#drag_line").remove();
                        $("#ghost").remove();
                    }
                    $("body").removeClass('dragging').enableSelection().unbind('mousemove').unbind('mouseup');
                }
            });

        });

        return this;
    });

    /* Every time the user expands or collapses a part of the tree, we remember
       the current state of the tree so we can restore it on a reload.
       Note: We might use html5's session storage? */
    function storeCollapsedNodes(nodes) {
        $.cookie('feincms_collapsed_nodes', "[" + nodes.join(",") + "]", { expires: 7 });
    }

    function retrieveCollapsedNodes() {
        var n = $.cookie('feincms_collapsed_nodes');
        if(n != null) {
            try {
                n = $.parseJSON(n);
            } catch(e) {
                n = null;
            }
        }
        return n;
    }

    function expandOrCollapseNode(item) {
        var show = true;

        if(!item.hasClass('children'))
            return;

        var itemId = extractItemId(item.attr('id'));

        if(!isExpandedNode(itemId)) {
            item.removeClass('closed');
            markNodeAsExpanded(itemId);
        } else {
            item.addClass('closed');
            show = false;
            markNodeAsCollapsed(itemId);
        }

        storeCollapsedNodes(feincms.collapsed_nodes);

        doToggle(itemId, show);
    }

    // bind the collapse all children event
    $.extend($.fn.bindCollapseTreeEvent = function() {
        $(this).click(function() {
            rlist = $("#result_list");
            rlist.hide();
            $('tbody tr', rlist).each(function(i, el) {
                var marker = $('.page_marker', el);
                if(marker.hasClass('children')) {
                    var itemId = extractItemId(marker.attr('id'));
                    doToggle(itemId, false);
                    marker.addClass('closed');
                    markNodeAsCollapsed(itemId);
                }
            });
            storeCollapsedNodes(feincms.collapsed_nodes);
            rlist.show();
            $('tbody', rlist).recolorRows();
        });
        return this;
    });

    // bind the open all children event
    $.extend($.fn.bindOpenTreeEvent = function() {
        $(this).click(function() {
            rlist = $("#result_list");
            rlist.hide();
            $('tbody tr', rlist).each(function(i, el) {
                var marker = $('span.page_marker', el);
                if(marker.hasClass('children')) {
                    var itemId = extractItemId($('span.page_marker', el).attr('id'));
                    doToggle(itemId, true);
                    marker.removeClass('closed');
                    markNodeAsExpanded(itemId);
                }
            });
            storeCollapsedNodes([]);
            rlist.show();
            $('tbody', rlist).recolorRows();
        });
        return this;
    });

    var changelist_tab = function(elem, event, direction) {
        event.preventDefault();
        elem = $(elem);
        var ne = (direction > 0) ? elem.nextAll(':visible:first') : elem.prevAll(':visible:first');
        if(ne) {
            elem.attr('tabindex', -1);
            ne.attr('tabindex', '0');
            ne.focus();
        }
    };

    function keyboardNavigationHandler(event) {
        // console.log('keydown', this, event.keyCode);
        switch(event.keyCode) {
            case 40: // down
                changelist_tab(this, event, 1);
                break;
            case 38: // up
                changelist_tab(this, event, -1);
                break;
            case 37: // left
            case 39: // right
                expandOrCollapseNode($(this).find('.page_marker'));
                $('#result_list tbody').recolorRows();
                break;
            case 13: // return
                where_to = extractItemId($('span', this).attr('id'));
                document.location = document.location.pathname + where_to + '/'
                break;
            default:
                break;
            };
    }

    // fire!
    var rlist = $("#result_list"),
        rlist_tbody = rlist.find('tbody');

    if($('tbody tr', rlist).length > 1) {
        rlist.hide();
        rlist_tbody.feinTree();

        rlist.find('.page_marker').on('click', function(event) {
            event.preventDefault();
            event.stopPropagation();

            expandOrCollapseNode($(this));

            rlist_tbody.recolorRows();
        });

        $('#collapse_entire_tree').bindCollapseTreeEvent();
        $('#open_entire_tree').bindOpenTreeEvent();

        // Disable things user cannot do anyway (object level permissions)
        non_editable_fields = $('.tree-item-not-editable', rlist).parents('tr');
        non_editable_fields.addClass('non-editable');
        $('input:checkbox', non_editable_fields).attr('disabled', 'disabled');
        $('a:first', non_editable_fields).click(function(e){e.preventDefault()});
        $('.drag_handle', non_editable_fields).removeClass('drag_handle');

        /* Enable focussing, put focus on first result, add handler for keyboard navigation */
        $('tr', rlist).attr('tabindex', -1);
        $('tbody tr:first', rlist).attr('tabindex', 0).focus();
        $('tr', rlist).keydown(keyboardNavigationHandler);

        feincms.collapsed_nodes = [];
        var storedNodes = retrieveCollapsedNodes();
        if(storedNodes == null) {
            $('#collapse_entire_tree').click();
        } else {
            for(var i=0; i<storedNodes.length; i++) {
                expandOrCollapseNode($('#page_marker-' + storedNodes[i]));
            }
        }
    }

    rlist.show();
    $('tbody', rlist).recolorRows();
});
