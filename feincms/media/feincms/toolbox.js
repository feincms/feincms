/* Contains universally useful functions */

/* Extract an object id (numeric) from a DOM id. Assumes that a "-" is used
   as delimiter. Returns either the id found or 0 if something went wrong.

       extract_item_id('foo_bar_baz-327') -> 327
 */
var extract_item_id = function(elem_id) {
    var i = elem_id.indexOf('-');
    if(i >= 0)
        return parseInt(elem_id.slice(i+1));

    return 0;
}

/* Given an html snippet (in text form), parses it to extract the id attribute,
   then replace the corresponding element in the page with the snippet. The
   first parameter is ignored (so the signature matches what $.each expects).

       replace_element(0, '<div id="replace_me">New Stuff!</div>')
 */
var replace_element = function(i, html) {
    var r_id = $(html).attr('id');
    $('#' + r_id).replaceWith(html);
}

/* Same as above, but processes an array of html snippets */
var replace_elements = function(data) {
    $.each(data, replace_element);
}

/* OnClick handler to toggle a boolean field via AJAX */
var inplace_toggle_boolean = function(item_id, attr) {
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


