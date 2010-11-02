feincms.jQuery(function($){
	// recolor tree after expand/collapse
	$.extend($.fn.recolorRows = function() {
		$('tr', this).removeClass('row1').removeClass('row2');
		$('tr:visible:even', this).addClass('row1');
		$('tr:visible:odd', this).addClass('row2');
	});

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
			var pageId = extract_item_id($('.page_marker', el).attr('id'));
			$(el).attr('id', 'item-' + pageId);
			if (feincms.tree_structure[pageId].length) {
			    $('.page_marker', el).addClass('children');
			}

			// set 'level' on rel attribute
			var pixels = $('.page_marker', el).css('width').replace(/[^\d]/ig,"");
			var rel = Math.round(pixels/18);
			$(el).attr('rel', rel);

			// add drag handle to actions col
			$(el).find('td:last').append(' <div class="drag_handle"></div>');
		});

	    $('div.drag_handle').bind('mousedown', function(event) {
			BEFORE = 0;
			AFTER = 1;
			CHILD = 2;
			CHILD_PAD = 20;
			var originalRow = $(event.target).closest('tr');
			var rowHeight = originalRow.height();
			var childEdge = $(event.target).offset().left + $(event.target).width();
			var moveTo = new Object();
			var expandObj = new Object();

			$("body").disableSelection().bind('mousemove', function(event) {
				// attach dragged item to mouse
				var cloned = originalRow.clone();
				if($('#ghost').length == 0) {
					$('<div id="ghost"></div>').appendTo('body');
				}
				$('#ghost').html(cloned).css({ 'opacity': .8, 'position': 'absolute', 'top': event.pageY, 'left': event.pageX-30, 'width': 600 });

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

				var top;

				// loop trough all rows
				$("tr", originalRow.parent()).each(function(index, element) {
					element = $(element);
					top = element.offset().top;

					// check if mouse is over a row
					if (event.pageY >= top && event.pageY <= top + rowHeight) {
						// check if collapsed children, if so, on hover with simple timeout
						if(
							$('span.page_marker', element).hasClass('children') &&
							$('span.page_marker', element).hasClass('closed')
						) {
							var id = extract_item_id($('span.page_marker', element).attr('id'));
							setTimeout(function() {
								doToggle(id, true);
								$('#result_list tbody').recolorRows();
								$('span.page_marker', element).removeClass('closed');
							}, 750);
						}

						var targetRow = null;
						var targetLoc;
						if(event.pageY >= top && event.pageY <= top + rowHeight / 2 && element.prev()) {
							// upper half row
							targetRow = element;
							targetLoc = BEFORE;
						} else if(event.pageY > top + rowHeight / 2 && event.pageY <= top + rowHeight) {
							// lower half row
							if(element.next().size() > 0) {
								next = element.next().attr('rel').replace(/[^\d]/ig,"")
							} else {
								next = 0;
							}

							if(next < element.attr('rel').replace(/[^\d]/ig,"") && event.pageX < 100) {
								targetRow = element;
								targetLoc = AFTER;
							} else {
								targetRow = element;
							 	targetLoc = CHILD;
							}
						}

						if(targetRow) {
							var padding = 30 + element.attr('rel') * CHILD_PAD;

							$("#drag_line").css({
								'width': targetRow.width() - padding - (targetLoc == CHILD ? CHILD_PAD : 0 ),
								'left': targetRow.offset().left + padding + (targetLoc == CHILD ? CHILD_PAD : 0),
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

			$("body").bind('mouseup', function(event) {
				var cutItem = extract_item_id(originalRow.find('.page_marker').attr('id'));
				var pastedOn = extract_item_id(moveTo.relativeTo.find('.page_marker').attr('id'));

				// get out early if items are the same
				if(cutItem != pastedOn) {
					var isParent = (moveTo.relativeTo.next().attr('rel') > moveTo.relativeTo.attr('rel'));
					// determine position
					if(moveTo.side == CHILD && !isParent) {
						var position = 'last-child';
					} else {
						var position = 'left';
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
				$("body").enableSelection().unbind('mousemove').unbind('mouseup');
			});

		});

		return this;
	});

    function expandOrCollapseNode(item) {
        var show = true;

        if(!item.hasClass('children'))
            return;

        var itemId = extract_item_id(item.attr('id'));

        if(!isExpandedNode(itemId)) {
            item.removeClass('closed');
            markNodeAsExpanded(itemId);
        } else {
            item.addClass('closed');
            show = false;
            markNodeAsCollapsed(itemId);
        }

        $.cookie('feincms_collapsed_nodes', feincms.collapsed_nodes);

        doToggle(itemId, show);

        $('#result_list tbody').recolorRows();
    }

	$.extend($.fn.feinTreeToggleItem = function() {
		$(this).click(function(event){
            expandOrCollapseNode($(this));
            if(event.stopPropagation) {
                event.stopPropagation();
            } else {
                event.cancelBubble = true;
            }

			return false;
		});
		return this;
	});

	// bind the collapse all children event
	$.extend($.fn.bindCollapseTreeEvent = function() {
		$(this).click(function() {
			$('#result_list tbody tr').each(function(i, el) {
				var marker = $('.page_marker', el);
				if(marker.hasClass('children')) {
                    var itemId = extract_item_id(marker.attr('id'));
					doToggle(itemId, false);
					marker.addClass('closed');
                    markNodeAsCollapsed(itemId);
				}
			});
            $.cookie('feincms_collapsed_nodes', feincms.collapsed_nodes);
			$('#result_list tbody').recolorRows();
		});
		return this;
	});

	// bind the open all children event
	$.extend($.fn.bindOpenTreeEvent = function() {
		$(this).click(function() {
			$('#result_list tbody tr').each(function(i, el) {
				var marker = $('span.page_marker', el);
				if(marker.hasClass('children')) {
                    var itemId = extract_item_id($('span.page_marker', el).attr('id'));
					doToggle(itemId, true);
					marker.removeClass('closed');
                    markNodeAsExpanded(itemId);
				}
			});
			$.cookie('feincms_collapsed_nodes', feincms.collapsed_nodes);
			$('#result_list tbody').recolorRows();
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
                break;
            case 13: // return
                where_to = extract_item_id($('span', this).attr('id'));
                document.location = document.location.pathname + where_to + '/'
                break;
            default:
                break;
            };
    }

	// fire!
	if($('#result_list tbody tr').length > 1) {
		$('#result_list tbody').feinTree();
		$('#result_list span.page_marker').feinTreeToggleItem();
		$('#collapse_entire_tree').bindCollapseTreeEvent();
		$('#open_entire_tree').bindOpenTreeEvent();

        /* Enable focussing, put focus on first result, add handler for keyboard navigation */
        $('#result_list tr').attr('tabindex', -1);
        $('#result_list tbody tr:first').attr('tabindex', 0).focus();
        $('#result_list tr').keydown(keyboardNavigationHandler);

		feincms.collapsed_nodes = [];
		var storedNodes = $.cookie('feincms_collapsed_nodes');
		if(storedNodes) {
			storedNodes = eval('[' + storedNodes + ']');
			for(var i=0; i<storedNodes.length; i++) {
				$('#page_marker-' + storedNodes[i]).click();
			}
		}
	}
});