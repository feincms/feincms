(function($){
    $(function(){
        var admin_base = '/admin/page/page/';

        feincms.fe_init_animations();

        $("#fe_tools > a").live("click", function() {
            var fe_box = $(this).parents('div.fe_box');

            if (this.id == 'fe_tools_edit') {
                res = fe_box.attr('id').match(/([^\-]+)-(\d+)-(\d+)/);

                window.open(admin_base+res[2]+'|'+res[1]+'|'+res[3]+'/',
                    'fe_editor',
                    'height=500,width=800,resizable=yes,scrollbars=yes');
            }

            return false;
        });
    });

    feincms.fe_init_animations = function() {
        var fe_tools = $('#fe_tools');
        $('.fe_box').hover(
            function(){
                $(this).css('background', '#e8e8ff').animate({'opacity': 1}, 100).append(fe_tools);
                fe_tools.show();
            },
            function(){
                $(this).animate({'opacity': 0.6}, 100).css('background', 'none');
                fe_tools.hide();
            }
        );
    }

    feincms.fe_update_content = function(identifier, content) {
        var region = $('#' + identifier);
        region.animate({'opacity': 0}).html(content);
        region.animate({'opacity': 1.5}).animate({'opacity': 0.6});
        feincms.fe_init_animations();
    }
})(feincms.jQuery);
