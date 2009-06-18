$(document).ready(function(){
    $("#main_wrapper > .navi_tab").click(function(){
        var elem = $(this);
        $("#main_wrapper > .navi_tab").removeClass("tab_active");
        elem.addClass("tab_active");
        $("#main > div:visible").hide();

        var tab_str = elem.attr("id").substr(0, elem.attr("id").length-4);
        $('#'+tab_str+'_body').show();
        ACTIVE_REGION = REGIONS.indexOf(tab_str);

        if (tab_str == "settings")
            $(".machine-control").hide();
        else
            $(".machine-control").show();

        // make it possible to open current tab on page reload
        window.location.hash = '#'+tab_str+'_tab';
    });

    $(".order-machine-add-button").livequery('click', function(){
        var select = $(this).prev();
        var modvar = select.val();
        var modname = select.children("option:selected").html();
        var total_forms = $('#id_'+modvar+'-TOTAL_FORMS');
        var last_id = parseInt(total_forms.val()) - 1;
        var form = $("#"+modvar+"_set_item_"+last_id);

        // update formset bookkeeping value
        total_forms.val(last_id+2);
        create_new_spare_form(form, modvar, last_id);
        region_append(ACTIVE_REGION, form, modname, modvar);
        set_item_field_value(form, "region-choice-field", ACTIVE_REGION);

        attach_dragdrop_handlers();
        init_contentblocks();
    });

    $(".order-machine-move-button").livequery('click', function(){
        var moveTo = $(this).prev().val();
        move_item(REGIONS.indexOf(moveTo), $("#main div.order-machine div.active-item"));
    });

    $(".item-delete").livequery('click',function(){
        popup_bg = '<div class="popup_bg"></div>';
        $("body").append(popup_bg);
        var item = $(this).parents(".order-item");
        jConfirm(DELETE_MESSAGES[0], DELETE_MESSAGES[1], function(r) {
            if (r==true) {
                set_item_field_value(item,"delete-field","checked");
                item.fadeOut(200);
            }
            $(".popup_bg").remove();
        });
    });

    $(".change-template").livequery('click',function(){
        popup_bg = '<div class="popup_bg"></div>';
        $("body").append(popup_bg);
        jConfirm(CHANGE_TEMPLATE_MESSAGES[1], CHANGE_TEMPLATE_MESSAGES[0], function(r) {
            if (r==true) {
                var items = $(".panel").children(".order-machine").children();
                move_item(0, items);
                $(".submit_form").click();
            } else {
                $(".popup_bg").remove();
            }
        });
    });

    $(".item-minimize").livequery('click',function(){
        var item = $(this).parent().next();
        if (item.is(":visible")) {
            $(this).html('<img src="'+IMG_ARROW_RIGHT_PATH+'" />');
            item.slideUp(200);
        } else {
            $(this).html('<img src="'+IMG_ARROW_DOWN_PATH+'" />');
            item.slideDown(200);
        }
    });

    $(".order-item").livequery('click',function(){
        $(".order-item.active-item").removeClass("active-item");
        $(this).addClass("active-item");
    });

    $(".submit_form").livequery('click',function(){
        zucht_und_ordnung(false);
        var form = $(this).parents('form');
        form.attr('action', form.attr('action')+window.location.hash);
        return true;
    });

});
