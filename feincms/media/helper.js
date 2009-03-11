function region_append(region, obj, modname) {
    var wrp = [];
    wrp.push('<div class="order-item"><div class="item-header">');
    if (obj.children(":visible").length > 0)
        wrp.push('<div class="item-minimize"><img src="'+IMG_ARROW_DOWN_PATH+'" /></div>');
    else
        wrp.push('<div class="item-minimize-disabled"><img src="'+IMG_CIRCLE_PATH+'" /></div>');
    wrp.push('<span>' + modname + '</span><img class="handle" src='+IMG_MOVE_PATH+' />');
    wrp.push('<img class="item-delete" src="'+IMG_DELETELINK_PATH+'" />');
    wrp.push('</div><div class="item-content"></div></div>');

    $("#"+REGIONS[region]+"_body").children(".order-machine").append(wrp.join(""))
        .children(".order-item:last").children(".item-content").append(obj);
}

function create_new_from_form(form, modvar, last_id) {
    var new_form = form.html().replace(
        new RegExp(modvar+'-'+last_id, 'g'),
        modvar+'-'+(last_id+1));
    new_form = '<div id="'+modvar+'_set_item_'+(last_id+1)+'">'+new_form+'</div>';
    $("#"+modvar+"_set").append(new_form);
}

function get_item_field_value(item,field) {
    // item: DOM object created by 'region_append' function
    // field: "order-field" | "delete-field" | "region-field"
    if (field=="delete-field")
        return item.find("."+field).attr("checked");
    else
        return item.find("."+field).val();
}

function set_item_field_value(item,field, value) {
    // item: DOM object created by 'region_append' function
    // field: "order-field" | "delete-field" | "region-field"
    if (field=="delete-field")
        item.find("."+field).attr("checked",value);
    else if (field=="region-choice-field") {
        var old_region_id = REGION_MAP.indexOf(item.find("."+field).val());
        item.find("."+field).val(REGION_MAP[value]);

        old_region_item = $("#"+REGIONS[old_region_id]+"_body");
        old_region_item.children(".empty-machine-msg").hide();
        if (old_region_item.children(".order-machine").children().length == 0)
            old_region_item.children(".empty-machine-msg").show();

        new_region_item = $("#"+REGIONS[value]+"_body");
        new_region_item.children(".empty-machine-msg").hide();
    }
    else
        item.find("."+field).val(value);
}

function move_item (region_id, item) {
    poorify_rich(item);
    $("#"+REGIONS[region_id]+"_body").children(".order-machine").append(item);
    set_item_field_value(item, "region-choice-field", region_id);
    richify_poor(item);
}

function poorify_rich(item){
    item.children(".item-content").hide();
    if (item.find("div[id^=richtext]").length > 0) {
        var editor_id = item.find(".mceEditor").prev().attr("id");
        tinyMCE.execCommand('mceRemoveControl',false,editor_id);
    }
}
function richify_poor(item){
    item.children(".item-content").show();
    if (item.find("div[id^=richtext]").length > 0) {
        var editor_id = item.find('textarea[name*=richtext]:visible').attr("id");
        tinyMCE.execCommand('mceAddControl',false,editor_id);
    }
}

function zucht_und_ordnung(move_item) {
    for (var i=0; i<REGIONS.length;i++) {
        var container = $("#"+REGIONS[i]+"_body .order-machine");
        for (var j=0; j<container.children().length; j++) {
            if (move_item)
                container.find(".order-field[value="+j+"]").parents(".order-item").appendTo(container);
            else
                set_item_field_value(container.find(".order-item:eq("+j+")"),"order-field",j);
        }
    }
}


