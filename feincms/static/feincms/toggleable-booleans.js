django.jQuery.ajaxSetup({
    crossDomain: false,  // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type))) {
            xhr.setRequestHeader("X-CSRFToken", document.cookie.match(/csrftoken=(.+?)\b/)[1]);
        }
    }
});

django.jQuery(function($){
    $(document.body).on('click', '[data-inplace]', function() {
        var elem = $(this),
            id = elem.data('inplace-id'),
            attr = elem.data('inplace-attribute');

        $.ajax({
            url: ".",
            type: "POST",
            dataType: "json",
            data: {
                'cmd': 'toggle_boolean',
                'item_id': id,
                'attr': attr
            },
            success: function(data) {
                $.each(data, function(i, html) {
                    var r_id = $(html).attr('id');
                    $('#' + r_id).replaceWith(html);
                });
            },

            error: function(xhr, status, err) {
                alert("Unable to toggle " + attr + ": " + xhr.responseText);
            }
        });
    });
});
