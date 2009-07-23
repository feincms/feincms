if(typeof(Array.prototype.indexOf) == 'undefined') {
    // indexOf() function prototype for IE6/7/8 compatibility, taken from 
    // JavaScript Standard Library - http://www.devpro.it/JSL/
    Array.prototype.indexOf=function(elm,i){
        var j=this.length;
        if(!i)i=0;
        if(i>=0){while(i<j){if(this[i++]===elm){
            i=i-1+j;j=i-j;
        }}}
        else
            j=this.indexOf(elm,j+i);
        return j!==this.length?j:-1;
    }
}

function region_append(region, obj, modname) {
    var wrp = [];
    wrp.push('<fieldset class="module aligned order-item">');
    wrp.push('<h2><img class="item-delete" src="'+IMG_DELETELINK_PATH+'" /><span class="handle"></span> '+modname+' &nbsp;(<span class="collapse">'+gettext('Hide')+'</span>)</h2>');
    wrp.push('<div class="item-content"></div>');
    wrp.push('</fieldset>');

    $("#"+REGION_MAP[region]+"_body").children("div.order-machine").append(wrp.join(""))
        .children("fieldset.order-item:last").children(".item-content").append(obj);
}

function create_new_spare_form(form, modvar, last_id) {
    // create new spare form
    var new_form = form.html().replace(
        new RegExp(modvar+'-'+last_id, 'g'),
        modvar+'-'+(last_id+1));
    new_form = '<div id="'+modvar+'_set_item_'+(last_id+1)+'">'+new_form+'</div>';
    $("#"+modvar+"_set").append(new_form);
}

function set_item_field_value(item, field, value) {
    // item: DOM object created by 'region_append' function
    // field: "order-field" | "delete-field" | "region-choice-field"
    if (field=="delete-field")
        item.find("."+field).attr("checked",value);
    else if (field=="region-choice-field") {
        var old_region_id = REGION_MAP.indexOf(item.find("."+field).val());
        item.find("."+field).val(REGION_MAP[value]);

        old_region_item = $("#"+REGION_MAP[old_region_id]+"_body");
        if (old_region_item.children("div.order-machine").children().length == 0)
            old_region_item.children("div.empty-machine-msg").show();
        else
            old_region_item.children("div.empty-machine-msg").hide();

        new_region_item = $("#"+REGION_MAP[value]+"_body");
        new_region_item.children("div.empty-machine-msg").hide();
    }
    else
        item.find("."+field).val(value);
}

function move_item (region_id, item) {
    poorify_rich(item);
    $("#"+REGION_MAP[region_id]+"_body").children("div.order-machine").append(item);
    set_item_field_value(item, "region-choice-field", region_id);
    richify_poor(item);
}

function poorify_rich(item){
    item.children(".item-content").hide();
    if (item.find("div[id^=richtext]").length > 0) {
        var editor_id = item.find(".mceEditor").prev().attr("id");
        tinyMCE.execCommand('mceRemoveControl', false, editor_id);
    }
}
function richify_poor(item){
    item.children(".item-content").show();
    if (item.find("div[id^=richtext]").length > 0) {
        var editor_id = item.find('textarea[name*=richtext]:visible').attr("id");
        tinyMCE.execCommand('mceAddControl', false, editor_id);
    }
}

function zucht_und_ordnung(move_item) {
    for (var i=0; i<REGION_MAP.length;i++) {
        var container = $("#"+REGION_MAP[i]+"_body div.order-machine");
        for (var j=0; j<container.children().length; j++) {
            if (move_item)
                container.find("input.order-field[value="+j+"]").parents("fieldset.order-item").appendTo(container);
            else
                set_item_field_value(container.find("fieldset.order-item:eq("+j+")"), "order-field", j);
        }
    }
}

function attach_dragdrop_handlers() {
    // hide content on drag n drop
    $("#main h2 span.handle").mousedown(function(){
        poorify_rich($(this).parents("fieldset.order-item"));
    });
    $("#main h2 span.handle").mouseup(function(){
        richify_poor($(this).parents("fieldset.order-item"));
    });
}

function init_contentblocks() {
    for(var i=0; i<contentblock_init_handlers.length; i++)
        contentblock_init_handlers[i]();
}


$(document).ready(function(){
    $("#main_wrapper > .navi_tab").click(function(){
        var elem = $(this);
        $("#main_wrapper > .navi_tab").removeClass("tab_active");
        elem.addClass("tab_active");
        $("#main > div:visible, #main > fieldset:visible").hide();

        var tab_str = elem.attr("id").substr(0, elem.attr("id").length-4);
        $('#'+tab_str+'_body').show();
        ACTIVE_REGION = REGION_MAP.indexOf(tab_str);

        if (tab_str == "settings")
            $(".machine-control").hide();
        else
            $(".machine-control").show();

        // make it possible to open current tab on page reload
        window.location.hash = '#tab_'+tab_str;
    });

    $("input.order-machine-add-button").click(function(){
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

    $("input.order-machine-move-button").click(function(){
        var moveTo = $(this).prev().val();
        move_item(REGION_MAP.indexOf(moveTo), $("#main div.order-machine fieldset.active-item"));
    });

    $("h2 img.item-delete").live('click', function(){
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

    $('h2 span.collapse').live('click', function(){
        var node = this;
        $(this.parentNode.parentNode).children('.item-content').slideToggle(function(){
            $(node).text(gettext($(this).is(':visible') ? 'Hide' : 'Show'));
        });
        return false;
    });

    $("input.change-template").click(function(){
        popup_bg = '<div class="popup_bg"></div>';
        $("body").append(popup_bg);
        jConfirm(CHANGE_TEMPLATE_MESSAGES[1], CHANGE_TEMPLATE_MESSAGES[0], function(r) {
            if (r==true) {
                var items = $(".panel").children(".order-machine").children();
                move_item(0, items);
                $('form').submit();
            } else {
                $(".popup_bg").remove();
            }
        });
    });

    $("fieldset.order-item").live('click', function(){
        if(!$(this).hasClass('active-item')) {
            $("fieldset.active-item").removeClass("active-item");
            $(this).addClass("active-item");
        }
    });

    $('form').submit(function(){
        zucht_und_ordnung(false);
        var form = $(this);
        form.attr('action', form.attr('action')+window.location.hash);
        return true;
    });

    // move contents into their corresponding regions and do some simple formatting
    $("div[id$=_set]").children().each(function(){
        var elem = $(this);

        if (!(elem.hasClass("header"))) {
            elem.find("input[name$=-region]").addClass("region-choice-field");
            elem.find("input[name$=-DELETE]").addClass("delete-field").parents("div.form-row").hide();
            elem.find("input[name$=-ordering]").addClass("order-field");

            var region_id = elem.find(".region-choice-field").val();
            region_id = REGION_MAP.indexOf(region_id);
            var content_type = elem.attr("id").substr(0, elem.attr("id").indexOf("_"));
            region_append(region_id,elem, CONTENT_NAMES[content_type]);
            set_item_field_value(elem,"region-choice-field",region_id)
        }
    });
    // register regions as sortable for drag N drop
    $(".order-machine").sortable({
        handle: '.handle',
        helper: 'clone',
        placeholder: 'highlight',
        stop: function(event, ui) {
            richify_poor($(ui.item));
        }
    });

    attach_dragdrop_handlers();

    if(window.location.hash) {
        $('#'+window.location.hash.substr(5)+'_tab').trigger('click');
    } else {
        $('#main_wrapper>div.navi_tab:first-child').trigger('click');
    }

    // bring order to chaos
    zucht_und_ordnung(true);

    $('#inlines').hide();
});

$(window).load(function(){init_contentblocks()});
