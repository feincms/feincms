feincms.jQuery(function($){
	$.extend($.fn.disableTextSelect = function() {
		return this.each(function(){
			if($.browser.mozilla){//Firefox
				$(this).css('MozUserSelect','none');
			}else if($.browser.msie){//IE
				$(this).bind('selectstart',function(){return false;});
			}else{//Opera, etc.
				$(this).mousedown(function(){return false;});
			}
		});
	});
	
	$.extend($.fn.recolorRows = function() {
		$(this).removeClass('row1').removeClass('row2');
		$(':visible:even', this).addClass('row1');
		$(':visible:odd', this).addClass('row2');
		return true;
	});
	
	$.extend($.fn.feinTree = function() {
		$('tr', this).each(function(i, el) {
			var pixels = $(el).find('.page_marker').css('width').replace(/[^\d]/ig,"");
			$(el).attr('rel', Math.round(pixels/18));
		});
	    $(this).bind('mousedown', function(event) {
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
					$('<div id="ghost"></div>"').appendTo('body');
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
				var isParent = (moveTo.relativeTo.next().attr('rel') > moveTo.relativeTo.attr('rel'))
				if(moveTo.side == 2 && !isParent) {
					var position = 'last-child';
				} else {
					var position = 'left';
				}
				
				$.post('.', {
					'__cmd': 'move_node',
					'position': position,
					'cut_item': cutItem,
					'pasted_on': pastedOn,
				}, function(data) {
					if(data == 'OK') {
						window.location.reload();
					} else {
						alert(data);
					}
				});
				$("body").unbind('mousemove').unbind('mouseup');
			});
		});
	});
	
	
	
	// bind the collapse all children event
	$.extend($.fn.bindCollapseTreeEvent = function() {
		$(this).click(function() {
			$('#result_list tbody tr').each(function(i, el) {
				if($(el).attr('rel') > 1) {
					$(el).hide();
				}
			}).recolorRows();
		});
		
	});
	
	// bind the open all chilren event
	$.extend($.fn.bindOpenTreeEvent = function() {
		$(this).click(function() {
			$('#result_list tbody tr').each(function(i, el) {
				if($(el).attr('rel') > 1) {
					$(el).show();
				}
			}).recolorRows();
		});
		recolerTableRows();
	});
	
	// fire!		
	$('#result_list tbody').feinTree();
	$('#collapse_entire_tree').bindCollapseTreeEvent();
	$('#open_entire_tree').bindOpenTreeEvent();
	$('#result_list').disableTextSelect();
});