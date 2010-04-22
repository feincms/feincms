if(!Array.indexOf) {
    Array.prototype.indexOf = function(obj) {
        for(var i=0; i<this.length; i++) {
            if(this[i]==obj) {
                return i;
            }
        }
        return -1;
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

    item.find('div.item-content textarea[class^=item-richtext-]').each(function(){
        var field = $(this);
        var classes = field.attr('class').split(' ');
        $.each(classes, function() {
            if(this.match('^item-richtext-')) {
                var remove_func = undefined;
                try { remove_func = eval('feincms_richtext_remove_' + this.substr(14)); } catch(e) {}
                if(typeof(remove_func) == 'function'){
                    remove_func(field);
                }
            }
        });
    });

    $('input[type=radio][checked]', item).addClass('radiochecked');
}

function richify_poor(item){
    item.children(".item-content").show();

    item.find('div.item-content textarea[class^=item-richtext-]').each(function(){
        var field = $(this);
        var classes = field.attr('class').split(' ');
        $.each(classes, function() {
            if(this.match('^item-richtext-')) {
                var add_func = undefined;
                try { add_func = eval('feincms_richtext_add_' + this.substr(14)); } catch(e) {}
                if(typeof(add_func) == 'function'){
                    add_func(field);
                }
            }
        });
    });

    $('input.radiochecked', item).removeClass('radiochecked').trigger('click');
}

function sort_by_ordering(e1, e2) {
  var v1 = parseInt($('.order-field', e1).val()) || 0;
  var v2 = parseInt($('.order-field', e2).val()) || 0;
  return  v1 > v2 ? 1 : -1;
};

function give_ordering_to_content_types() {
  for (var i=0; i<REGION_MAP.length;i++) {
    var container = $("#"+REGION_MAP[i]+"_body div.order-machine");
    for (var j=0; j<container.children().length; j++) {
      set_item_field_value(container.find("fieldset.order-item:eq("+j+")"), "order-field", j);
    }
  }
}

function order_content_types_in_regions() {
  for (var i=0; i<REGION_MAP.length;i++) {
    var container = $("#"+REGION_MAP[i]+"_body div.order-machine");
    container.children().sort(sort_by_ordering).each(function() {
      container.append(this);
    });
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


// global variable holding the current template key
var current_template;

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
        var active_item = $("#main div.order-machine fieldset.active-item");

        if (!active_item.length) {
            jAlert(NO_ITEM_SELECTED_MESSAGE);
            return false;
        }

        move_item(REGION_MAP.indexOf(moveTo), active_item);
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

    current_template = $('input[name=template_key][checked], select[name=template_key]').val();

    function on_template_key_changed(){
        var input_element = this;
        var new_template = this.value;

        if(current_template==new_template)
            // Selected template did not change
            return false;

        current_regions = template_regions[current_template];
        new_regions = template_regions[new_template];

        not_in_new = [];
        for(var i=0; i<current_regions.length; i++)
            if(new_regions.indexOf(current_regions[i])==-1)
                not_in_new.push(current_regions[i]);

        popup_bg = '<div id="popup_bg"></div>';
        $("body").append(popup_bg);

        var msg = CHANGE_TEMPLATE_MESSAGES[1];

        if(not_in_new.length) {
            msg = interpolate(CHANGE_TEMPLATE_MESSAGES[2], {
                'source_regions': not_in_new,
                'target_region': new_regions[0]
            }, true);
        }

        jConfirm(msg, CHANGE_TEMPLATE_MESSAGES[0], function(ret) {
            if(ret) {
                for(var i=0; i<not_in_new.length; i++) {
                    var items = $('#'+not_in_new[i]+'_body div.order-machine').children();
                    move_item(0, items);
                }

                input_element.checked = true;

                $('form').append('<input type="hidden" name="_continue" value="1" />').submit();
            } else {
                $("div#popup_bg").remove();
            }
        });

        return false;
    }

    $('input[type=radio][name=template_key]').click(on_template_key_changed);
    $('select[name=template_key]').change(on_template_key_changed);

    $("fieldset.order-item").live('click', function(){
        if(!$(this).hasClass('active-item')) {
            $("fieldset.active-item").removeClass("active-item");
            $(this).addClass("active-item");
        }
    });

    $('form').submit(function(){
        give_ordering_to_content_types();
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

    order_content_types_in_regions();

    $('#inlines').hide();

    var errors = $('#main div.errors');

    if(errors.length) {
        var id = errors.parents('fieldset[id$=_body], div[id$=_body]').attr('id');
        $('#'+id.replace('_body', '_tab')).trigger('click');
    } else {
        if(window.location.hash) {
            var tab = $('#'+window.location.hash.substr(5)+'_tab');

            if(tab.length) {
                tab.trigger('click');
                return;
            }
        }

        $('#main_wrapper>div.navi_tab:first-child').trigger('click');
    }
});

$(window).load(function(){init_contentblocks()});
