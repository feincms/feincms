(function($){
    $(function(){
        var admin_base = '/admin/page/page/';

        feincms.fe_init_animations();

        $("#fe_tools > a").live("click", function() {
            var fe_box = $(this).parents('div.fe_box');

            if (this.id == 'fe_tools_edit') {
                res = fe_box.attr('id').match(/([^\-]+)-(\d+)-(\d+)/);
                var base = admin_base;
                var fe_box_class = fe_box.attr("class");
                if (fe_box_class) {
                	var fe_path = fe_box_class.match(/fe_path_([\w_]+)/);
                	if (fe_path) {
                		base = "/"+ fe_path[1].replace(/_/g,"/") + "/";
                	}
                }
                window.open(base+res[2]+'|'+res[1]+'|'+res[3]+'/',
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
