feincms.jQuery(function($){
	/*
	 * jQuery Untils - v1.1 - 2/18/2010
	 * http://benalman.com/projects/jquery-untils-plugin/
	 *
	 * Copyright (c) 2010 "Cowboy" Ben Alman
	 * Dual licensed under the MIT and GPL licenses.
	 * http://benalman.com/about/license/
	 */
	(function($){$.each({nextUntil:"nextAll",prevUntil:"prevAll",parentsUntil:"parents"},function(a,b){$.fn[a]=function(e,f){var c=$([]),d=this.get();if(a.indexOf("p")===0&&d.length>1){d=d.reverse()}$.each(d,function(){$(this)[b]().each(function(){var g=$(this);if(g.is(e)){return false}else{if(!f||g.is(f)){c=c.add(this)}}})});return this.pushStack(c,a,e+(f?","+f:""))}})})(jQuery);

	// disable text selection
	$.extend($.fn.disableTextSelect = function() {
		return this.each(function() {
			if($.browser.mozilla) {//Firefox
				$(this).css('MozUserSelect', 'none');
			} else if($.browser.msie) {//IE
				$(this).bind('selectstart', function(){ return false; });
			} else {//Opera, etc.
				$(this).mousedown(function(){ return false; });
			}
		});
	});

	// recolor tree after expand/collapse
	$.extend($.fn.recolorRows = function() {
		$('tr', this).removeClass('row1').removeClass('row2');
		$('tr:visible:even', this).addClass('row1');
		$('tr:visible:odd', this).addClass('row2');
	});

    var extract_id = function(s) {
        return s.match(/-(\d+)$/)[1];
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
	    var all_rows = $('tr', this);
	    var last_page_marker = null;
	    var last_rel = null;

		all_rows.each(function(i, el) {
		    var $row = $(el);
		    var $page_marker = $row.find('.page_marker');
		    var page_id = extract_id($page_marker.attr('id'));

		    $row.attr('id', 'item-' + page_id);
		    if (feincms.tree_structure[page_id].length)
		        $page_marker.addClass('children');

			// set 'level' on rel attribute
			var pixels = $page_marker.css('width').replace(/[^\d]/ig,"");
			var rel = Math.round(pixels/18);
			$row.attr('rel', rel);

			// add drag handle to actions col
			$row.find('td:last').append(' <div class="drag_handle"></div>');
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

			$("body").bind('mousemove', function(event) {
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
						// todo: check if collapsed children, if so, on hover with simple timeout
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
								'top': targetRow.offset().top + (targetLoc == AFTER || targetLoc == CHILD ? rowHeight: 0) -1,
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
				var cutItem = originalRow.find('.page_marker').attr('id').replace(/[^\d]/ig,"");
				var pastedOn = moveTo.relativeTo.find('.page_marker').attr('id').replace(/[^\d]/ig,"");

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
						'pasted_on': pastedOn,
					}, function(data) {
					    window.location.reload();
					});
				} else {
					$("#drag_line").remove();
					$("#ghost").remove();
				}
				$("body").unbind('mousemove').unbind('mouseup');
			});

		});

		return this;
	});

	$.extend($.fn.feinTreeToggleItem = function() {
        $(this).click(function(event){
            var show = true;
            var item = $(this);
            var item_id = extract_id(this.id);

            if (item.hasClass('closed')) {
                item.removeClass('closed');
                feincms.collapsed_nodes[item_id] = false;
            } else {
                item.addClass('closed');
                show = false;
                feincms.collapsed_nodes[item_id] = true;
            }

            function do_toggle(id, show) {
                var children = feincms.tree_structure[id];
                for (var i=0; i<children.length; ++i) {
                    var child_id = children[i];

                    if (show) {
                        $('#item-' + child_id).show();

                        // only reveal children if current node is not collapsed
                        if (!feincms.collapsed_nodes[child_id])
                            do_toggle(child_id, show);
                    } else {
                        $('#item-' + child_id).hide();

                        // always recursively hide children
                        do_toggle(child_id, show);
                    }
                }
            }

            do_toggle(item_id, show);

            if (event.stopPropagation) {
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
				if($(el).attr('rel') > 1) {
					$(el).hide();
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
				if($(el).attr('rel') > 1) {
					$(el).show();
				}
			});
			$('#result_list tbody').recolorRows();
		});
		return this;
	});

	// fire!
	if($('#result_list tbody tr').length > 1) {
		$('#result_list tbody').feinTree().disableTextSelect();
		$('#result_list span.page_marker').feinTreeToggleItem();
		$('#collapse_entire_tree').bindCollapseTreeEvent();
		$('#open_entire_tree').bindOpenTreeEvent();

		feincms.collapsed_nodes = {};
	}
});
