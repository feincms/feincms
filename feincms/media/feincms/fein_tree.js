feincms.jQuery(function($){
	// recolor tree after expand/collapse
	$.extend($.fn.recolorRows = function() {
		$('tr', this).removeClass('row1').removeClass('row2');
		$('tr:visible:even', this).addClass('row1');
		$('tr:visible:odd', this).addClass('row2');
	});

	// extract id
	function extractId(s) {
		return s.match(/-(\d+)$/)[1];
	}

	// toggle children
	function doToggle(id, show) {
		var children = feincms.tree_structure[id];
		for (var i=0; i<children.length; ++i) {
			var childId = children[i];
			if(show) {
				$('#item-' + childId).show();
				// only reveal children if current node is not collapsed
				if(feincms.collapsed_nodes.indexOf(childId) == -1) {
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
			var pageId = extractId($('.page_marker', el).attr('id'));
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
							var id = extractId($('span.page_marker', element).attr('id'));
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
				var cutItem = extractId(originalRow.find('.page_marker').attr('id'));
				var pastedOn = extractId(moveTo.relativeTo.find('.page_marker').attr('id'));

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

	$.extend($.fn.feinTreeToggleItem = function() {
		$(this).click(function(event){
			var show = true;
			var item = $(this);
			var itemId = extractId(this.id);

			if(item.hasClass('closed')) {
				item.removeClass('closed');

				// remove itemId from array of collapsed nodes
				for(var i=0; i<feincms.collapsed_nodes.length; ++i) {
					if (feincms.collapsed_nodes[i] == itemId)
					feincms.collapsed_nodes.splice(i, 1);
				}
			} else {
				item.addClass('closed');
				show = false;
				feincms.collapsed_nodes.push(itemId);
			}

			$.cookie('feincms_collapsed_nodes', feincms.collapsed_nodes);

			doToggle(itemId, show);

			if(event.stopPropagation) {
				event.stopPropagation();
			} else {
				event.cancelBubble = true;
			}

			$('#result_list tbody').recolorRows();
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
					doToggle(extractId(marker.attr('id')), false);
					marker.addClass('closed');
				}
			});
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
					doToggle(extractId($('span.page_marker', el).attr('id')), true);
					marker.removeClass('closed');
				}
			});
			$('#result_list tbody').recolorRows();
		});
		return this;
	});

	// fire!
	if($('#result_list tbody tr').length > 1) {
		$('#result_list tbody').feinTree();
		$('#result_list span.page_marker').feinTreeToggleItem();
		$('#collapse_entire_tree').bindCollapseTreeEvent();
		$('#open_entire_tree').bindOpenTreeEvent();
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