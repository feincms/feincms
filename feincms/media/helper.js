function region_append(region, obj, modname) {
    var contentSize = obj.children(":visible").length;
    var wrp = [];
    wrp[wrp.length] = '<div class="order-item"><div class="handle"></div><div class="item-header">';
    if (contentSize > 0)
        wrp[wrp.length] = '<div class="item-minimize"><img src="'+IMG_ARROW_DOWN_PATH+'" /></div>';
    else
        wrp[wrp.length] = '<div class="item-minimize-disabled"><img src="'+IMG_CIRCLE_PATH+'" /></div>';
    wrp[wrp.length] = '<span>' + modname + '</span>';
    wrp[wrp.length] = '<img class="item-delete" src="/media/img/admin/icon_deletelink.gif" />';

    wrp[wrp.length] = '</div><div class="item-content"></div></div>';

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
        return item.children(".item-content").children().children("."+field).attr("checked");
    else
        return item.children(".item-content").children().children("."+field).val();
}

function set_item_field_value(item,field, value) {
    // item: DOM object created by 'region_append' function
    // field: "order-field" | "delete-field" | "region-field"
    if (field=="delete-field")
        item.children(".item-content").children().children("."+field).attr("checked",value);
    else if (field=="region-choice-field")
        item.children(".item-content").children().children("."+field).val(REGION_MAP[value]);
    else
        item.children(".item-content").children().children("."+field).val(value);
}

function zucht_und_ordnung() {
    for (var i=0; i<REGIONS.length;i++) {
        var container = $("#"+REGIONS[i]+"_body .order-machine");
        for (var j=0; j<container.children().length; j++) {
            var item = container.children(".order-item:eq("+j+")");
            set_item_field_value(item,"order-field",j);
        }
    }
}


