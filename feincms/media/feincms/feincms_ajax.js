var ajax_links_selector = 'a.ajax';
var content_selector = '#main';
var animation_time = 300;
var navilevel_substring = 0; // how many chars from pathname are static (3 for languagecode like /de/)

/* needs feincms to be ajax-enabled:
 * 
 * feincms/views/base.py:
 * 
 * ...
 * 
 * def _build_page_response(page, request):
    extra_context = request._feincms_extra_context
    
    if request.is_ajax():
        template = os.path.join('ajax', page.template.path)
    else:
        template = page.template.path
    
    return render_to_response(template, {
        'feincms_page': page,
        }, context_instance=RequestContext(request, extra_context))
 * 
 * ...
 * 
 */
var first_call = true;

$(function(){
	$(ajax_links_selector).live('click', get_content);
});

$.address.externalChange(function(event) {
	if (!first_call || $.address.path() != '/') {
		var path_cleaned = location.pathname.substring(0, navilevel_substring);
		get_content(false, path_cleaned + event.value);
	} else {
		first_call = false;
	}
});

function get_content(event, url) {
	if (event) {
		event.preventDefault();
		link = $(event.target);
	}
	
	if (!url) {
		url = link.attr('rel');
	}
	
	$.address.value(url.substring(navilevel_substring));
	
	pre_ajax();
	
	setTimeout(function() {
		$.ajax({
			url		:	url,
			success	:	update_page,
			error	:	function(XMLHttpRequest, textStatus, errorThrown) {redirect_to_url(XMLHttpRequest, textStatus, errorThrown, url)},
			dataType:	'html'
			
		});
	});
}

function update_page(data, textStatus, XMLHttpRequest) {
	var title = $(data).filter('title').text();
	$.address.title(title);
		
	$(data).filter('div, h1, h2, h3, p, span').each(function(index) {
		var new_element = $(this);
		var old_element = $('#' + new_element.attr('id'))
		var new_class = new_element.attr('class');
		var old_class = old_element.removeClass('loading').attr('class');
		
		if (new_element.attr('id') == 'content') {
			new_element.addClass('loading');
		}
		
		if (new_class != old_class) {
			old_element.switchClass(old_class, new_class, animation_time);
			setTimeout(function() {
				old_element.replaceWith(new_element);
			}, animation_time);
		} else {		
			old_element.replaceWith(new_element);
		}
	});
	
	post_ajax();
}

function redirect_to_url(XMLHttpRequest, textStatus, errorThrown, url) {
	window.location = url;
}

function pre_ajax() {
	$(content_selector).addClass('loading');
}

function post_ajax() {
	setTimeout(function() {
		post_ajax_animations()
	}, 1000);
}

function post_ajax_animations() {
	$(content_selector).removeClass('loading');
}


