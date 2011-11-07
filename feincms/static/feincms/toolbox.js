/* Contains universally useful functions */

/* Extract an object id (numeric) from a DOM id. Assumes that a "-" is used
   as delimiter. Returns either the id found or 0 if something went wrong.

       extract_item_id('foo_bar_baz-327') -> 327
 */
function extract_item_id(elem_id) {
    var i = elem_id.indexOf('-');
    if(i >= 0)
        return parseInt(elem_id.slice(i+1), 10);

    return 0;
}

/* Given an html snippet (in text form), parses it to extract the id attribute,
   then replace the corresponding element in the page with the snippet. The
   first parameter is ignored (so the signature matches what $.each expects).

       replace_element(0, '<div id="replace_me">New Stuff!</div>')
 */
function replace_element(i, html) {
    var r_id = $(html).attr('id');
    $('#' + r_id).replaceWith(html);
}

/* Same as above, but processes an array of html snippets */
function replace_elements(data) {
    $.each(data, replace_element);
}

/* Setup django csrf-token for ajax calls, necessary since Django 1.2.5 */
/* See http://docs.djangoproject.com/en/1.2/releases/1.2.5/#csrf-exception-for-ajax-requests */

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});

/* OnClick handler to toggle a boolean field via AJAX */
function inplace_toggle_boolean(item_id, attr) {
    $.ajax({
      url: ".",
      type: "POST",
      dataType: "json",
      data: { '__cmd': 'toggle_boolean', 'item_id': item_id, 'attr': attr },

      success: replace_elements,

      error: function(xhr, status, err) {
          alert("Unable to toggle " + attr + ": " + xhr.responseText);
      }
    });

    return false;
}


