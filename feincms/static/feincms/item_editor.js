if(!Array.indexOf) {
    Array.prototype.indexOf = function(obj) {
        for(var i=0; i<this.length; i++) {
            if(this[i]==obj) {
                return i;
            }
        }
        return -1;
    };
}

(function($){
    // Patch up urlify maps to generate nicer slugs in german
    if(typeof(Downcoder) != "undefined"){
        Downcoder.Initialize() ;
        Downcoder.map["ö"] = Downcoder.map["Ö"] = "oe";
        Downcoder.map["ä"] = Downcoder.map["Ä"] = "ae";
        Downcoder.map["ü"] = Downcoder.map["Ü"] = "ue";
    }

    function feincms_gettext(s) {
        // Unfortunately, we cannot use Django's jsi18n view for this
        // because it only sends translations from the package
        // "django.conf" -- our own djangojs domain strings won't be
        // picked up

        if (FEINCMS_ITEM_EDITOR_GETTEXT[s])
            return FEINCMS_ITEM_EDITOR_GETTEXT[s];
        return s;
    }

    function create_new_item_from_form(form, modname, modvar){

        var fieldset = $("<fieldset>").addClass("module aligned order-item item-wrapper-" + modvar);
        var original_id_id = '#id_' + form.attr('id') + '-id';

        var wrp = ['<h2>'];
        // If original has delete checkbox or this is a freshly added CT? Add delete link!
        if($('.delete', form).length || !$(original_id_id, form).val()) {
            wrp.push('<img class="item-delete" src="'+IMG_DELETELINK_PATH+'" />');
        }
        wrp.push('<span class="handle"></span> <span class="modname">'+modname+'</span> &nbsp;(<span class="collapse">'+feincms_gettext('Hide')+'</span>)</h2>');
        wrp.push('<div class="item-content"></div>');
        fieldset.append(wrp.join(""));

        fieldset.children(".item-content").append(form); //relocates, not clone

        $("<div>").addClass("item-controls").appendTo(fieldset);

        return fieldset;
    }


    SELECTS = {};
    function save_content_type_selects() {
        $('#main>.panel').each(function() {
            SELECTS[this.id.replace(/_body$/, '')] = $("select[name=order-machine-add-select]", this).clone().removeAttr("name");
        });
    }

    function update_item_controls(item, target_region_id){
        var item_controls = item.find(".item-controls");
        item_controls.find(".item-control-units").remove(); // Remove all controls, if any.

        // (Re)build controls
        var control_units = $("<div>").addClass("item-control-units").appendTo(item_controls);

        // Insert control unit
        var insert_control = $("<div>").addClass("item-control-unit");
        var select_content = SELECTS[REGION_MAP[target_region_id]].clone();
        var insert_after = $("<input>").attr("type", "button").addClass("button").attr("value", feincms_gettext('After')).click(function(){
            var modvar = select_content.val();
            var modname = select_content.find("option:selected").html();
            var new_fieldset = create_new_fieldset_from_module(modvar, modname);
            add_fieldset(target_region_id, new_fieldset, {where:'insertAfter', relative_to:item, animate:true});
            update_item_controls(new_fieldset, target_region_id);
        });
        var insert_before = $("<input>").attr("type", "button").addClass("button").attr("value", feincms_gettext('Before')).click(function(){
            var modvar = select_content.val();
            var modname = select_content.find("option:selected").html();
            var new_fieldset = create_new_fieldset_from_module(modvar, modname);
            add_fieldset(target_region_id, new_fieldset, {where:'insertBefore', relative_to:item, animate:true});
            update_item_controls(new_fieldset, target_region_id);
        });
        insert_control.append("<span>" + feincms_gettext('Insert new:') + "</span>").append(" ").append(select_content).append(" ").append(insert_before).append(insert_after);
        control_units.append(insert_control);

        // Move control unit
        if (REGION_MAP.length > 1) {
            var wrp = [];
            wrp.push('<div class="item-control-unit move-control"><span>'+feincms_gettext('Move to')+': </span><select name="item-move-select">');

            for (var i=0; i < REGION_MAP.length; i++) {
                if (i != target_region_id) { // Do not put the target region in the list
                    wrp.push('<option value="'+REGION_MAP[i]+'">'+REGION_NAMES[i]+'</option>');
                }
            }
            wrp.push('</select><input type="button" class="button" value="'+feincms_gettext('Move')+'" /></div>');

            var move_control = $(wrp.join(""));
            move_control.find(".button").click(function(){
                var move_to = $(this).prev().val();
                move_item(REGION_MAP.indexOf(move_to), item);
            });
            control_units.append(move_control); // Add new one
        }

        // Controls animations
        item_controls.find("*").hide();
        var is_hidden = true;
        var mouseenter_timeout;
        var mouseleave_timeout;
        function hide_controls() {
            item_controls.find("*").fadeOut(400);
            is_hidden = true;
        }
        function show_controls() {
            item_controls.find("*").fadeIn(200);
            is_hidden = false;
        }
        item_controls.unbind('mouseleave'); // Unbind in case it's already been bound.
        item_controls.mouseleave(function() {
            clearTimeout(mouseenter_timeout);
            mouseleave_timeout = setTimeout(hide_controls, 200);
        });
        item_controls.unbind('mouseenter'); // Unbind in case it's already been bound.
        item_controls.mouseenter(function() {
            clearTimeout(mouseleave_timeout);
            if (is_hidden) mouseenter_timeout = setTimeout(show_controls, 200); // To prevent the control bar to appear when mouse accidentally enters the zone.
        });
    }


    function create_new_fieldset_from_module(modvar, modname) {
        var new_form = create_new_spare_form(modvar);
        return create_new_item_from_form(new_form, modname, modvar);
    }

    function add_fieldset(region_id, item, how){
        /* `how` should be an object.
           `how.where` should be one of:
         - 'append' -- last region
         - 'prepend' -- first region
         - 'insertBefore' -- insert before relative_to
         - 'insertAfter' -- insert after relative_to */

        // Default parameters
        if (how) $.extend({
            where: 'append',
            relative_to: undefined,
            animate: false
        }, how);

        item.hide();
        if(how.where == 'append' || how.where == 'prepend'){
            $("#"+ REGION_MAP[region_id] +"_body").children("div.order-machine")[how.where](item);
        }
        else if(how.where == 'insertBefore' || how.where == 'insertAfter'){
            if(how.relative_to){
                item[how.where](how.relative_to);
            }
            else{
                window.alert('DEBUG: invalid add_fieldset usage');
                return;
            }
        }
        else{
            window.alert('DEBUG: invalid add_fieldset usage');
            return;
        }
        set_item_field_value(item, "region-choice-field", region_id);
        init_contentblocks();

        if (how.animate) {
            item.fadeIn(800);
        }
        else {
            item.show();
        }
    }

    function create_new_spare_form(modvar) {
        var old_form_count = parseInt($('#id_'+modvar+'_set-TOTAL_FORMS').val(), 10);
        // **** UGLY CODE WARNING, avert your gaze! ****
        // for some unknown reason, the add-button click handler function
        // fails on the first triggerHandler call in some rare cases;
        // we can detect this here and retry:
        for(var i = 0; i < 2; i++){
            // Use Django's built-in inline spawing mechanism (Django 1.2+)
            // must use django.jQuery since the bound function lives there:
            django.jQuery('#'+modvar+'_set-group').find(
                'div.add-row > a').triggerHandler('click');
            var new_form_count = parseInt($('#id_'+modvar+'_set-TOTAL_FORMS').val(), 10);
            if(new_form_count > old_form_count){
                return $('#'+modvar+'_set-'+(new_form_count-1));
            }
        }
    }

    function set_item_field_value(item, field, value) {
        // item: DOM object for the item's fieldset.
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

    function move_item(region_id, item) {
        poorify_rich(item);
        item.fadeOut(800, function() {
            add_fieldset(region_id, item, {where:'append'});
            richify_poor(item);
            update_item_controls(item, region_id);
            item.show();
        });
    }

    function poorify_rich(item){
        item.children(".item-content").hide();

        for (var i=0; i<contentblock_move_handlers.poorify.length; i++)
            contentblock_move_handlers.poorify[i](item);
    }

    function richify_poor(item){
        item.children(".item-content").show();

        for (var i=0; i<contentblock_move_handlers.richify.length; i++)
            contentblock_move_handlers.richify[i](item);
    }

    function sort_by_ordering(e1, e2) {
      var v1 = parseInt($('.order-field', e1).val(), 10) || 0;
      var v2 = parseInt($('.order-field', e2).val(), 10) || 0;
      return  v1 > v2 ? 1 : -1;
    }

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

    function init_contentblocks() {
        for(var i=0; i<contentblock_init_handlers.length; i++)
            contentblock_init_handlers[i]();
    }

    function hide_form_rows_with_hidden_widgets(){
        /* This is not normally done in django -- the fields are shown
           with visible labels and invisible widgets, but FeinCMS used to
           use custom form rendering to hide rows for hidden fields.
           This is an attempt to preserve that behaviour. */
        $('div.feincms_inline div.form-row').each(function(){
            var child_count = $(this).find('*').length;
            var invisible_types = 'div, label, input[type=hidden], p.help';
            var invisible_count = $(this).find(invisible_types).length;
            if(invisible_count == child_count){
                $(this).addClass('hidden-form-row');
            }
        });
    }

    function init_content_type_buttons() {
        $('#main > .panel').each(function() {
            var $select = $('select[name=order-machine-add-select]', this),
                to_remove = [];

            for (var i=0; i<CONTENT_TYPE_BUTTONS.length; i++) {
                var c = CONTENT_TYPE_BUTTONS[i],
                    $option = $select.find('option[value=' + c.type + ']');

                if (!$option.length)
                    continue;

                var $button = $('<a href="#" class="actionbutton" />');
                $button.attr('title', CONTENT_NAMES[c.type]);

                $button.addClass(c.cssclass ? c.cssclass : c.type).bind('click', (function(c) {
                    return function() {
                        var fieldset = ItemEditor.add_content_to_current(c.type);
                        if (c.raw_id_picker) {
                            var id = fieldset.find('.related-lookup, span.mediafile').attr('id');

                            if (id) {
                                window.open(c.raw_id_picker,
                                    id_to_windowname(id.replace(/^lookup_/, '')),
                                    'height=500,width=800,resizable=yes,scrollbars=yes').focus();
                            }
                        }
                        if (c.after)
                            c.after.call(null, fieldset);
                        return false;
                    };
                })(c));

                $select.before($button);

                if (!c.keep)
                    to_remove.push($option);
            }

            for (var i=0; i<to_remove.length; i++)
                to_remove[i].remove();

            if ($select.find('option').length == 0) {
                // hide the content type select box and the add button if
                // the dropdown is empty now
                $select.hide().next().hide();
            }
        });
    }

    // global variable holding the current template key
    var current_template;

    $(document).ready(function($){
        hide_form_rows_with_hidden_widgets();

        $("#main_wrapper > .navi_tab").click(function(){
            var elem = $(this);
            $("#main_wrapper > .navi_tab").removeClass("tab_active");
            elem.addClass("tab_active");
            $("#main > div:visible, #main > fieldset:visible").hide();

            var tab_str = elem.attr("id").substr(0, elem.attr("id").length-4);
            $('#'+tab_str+'_body').show();
            ACTIVE_REGION = REGION_MAP.indexOf(tab_str);

            // make it possible to open current tab on page reload
            window.location.replace('#tab_'+tab_str);
        });

        // save content type selects for later use
        save_content_type_selects();

        $("input.order-machine-add-button").click(function(){
            var select_content = $(this).prev();
            var modvar = select_content.val();

            // bail out early if no content type selected
            if (!modvar)
                return;

            var modname = select_content.find("option:selected").html();
            var new_fieldset = create_new_fieldset_from_module(modvar, modname);
            add_fieldset(ACTIVE_REGION, new_fieldset, {where:'append', animate:true});
            update_item_controls(new_fieldset, ACTIVE_REGION);
        });

        $("h2 img.item-delete").live('click', function(){
            var popup_bg = '<div class="popup_bg"></div>';
            $("body").append(popup_bg);
            var item = $(this).parents(".order-item");
            jConfirm(DELETE_MESSAGES[0], DELETE_MESSAGES[1], function(r) {
                if (r==true) {
                    var in_database = item.find(".delete-field").length;
                    if(in_database==0){ // remove on client-side only
                        var id = item.find(".item-content > div").attr('id');

                        // poorify all contents
                        items = item.parents('.order-machine').find('.order-item');
                        items.each(function() {
                          poorify_rich($(this));
                        })

                        // remove content
                        django.jQuery('#'+id).find('a.inline-deletelink')
                          .triggerHandler('click');

                        // richify all contents again
                        items.each(function() {
                          richify_poor($(this));
                        })
                    }
                    else{ // saved on server, don't remove form
                        set_item_field_value(item,"delete-field","checked");
                    }
                    item.fadeOut(200, function() {
                      var region_item = $("#"+REGION_MAP[ACTIVE_REGION]+"_body");
                      if (region_item.children("div.order-machine").children(":visible").length == 0) {
                          region_item.children("div.empty-machine-msg").show();
                      }
                    });
                }
                $(".popup_bg").remove();
            });
        });

        $('h2 span.collapse').live('click', function(){
            var node = this;
            $(this.parentNode.parentNode).children('.item-content').slideToggle(function(){
                $(node).text(feincms_gettext($(this).is(':visible') ? 'Hide' : 'Show'));
            });
            return false;
        });

        current_template = $('input[name=template_key][checked], select[name=template_key]').val();

        function on_template_key_changed(){
            var input_element = this;
            var new_template = this.value;
            var form_element = $(input_element).parents('form');

            if(current_template==new_template)
                // Selected template did not change
                return false;

            var current_regions = template_regions[current_template];
            var new_regions = template_regions[new_template];

            var not_in_new = [];
            for(var i=0; i<current_regions.length; i++)
                if(new_regions.indexOf(current_regions[i])==-1)
                    not_in_new.push(current_regions[i]);

            var popup_bg = '<div id="popup_bg"></div>';
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
                        var body = $('#' + not_in_new[i] + '_body'),
                            machine = body.find('.order-machine'),
                            inputs = machine.find('input[name$=region]');

                        inputs.val(new_regions[0]);
                    }

                    input_element.checked = true;

                    form_element.append('<input type="hidden" name="_continue" value="1" />');
                    /* Simulate a click on the save button instead of form.submit(), so
                       that the submit handlers from FilteredSelectMultiple get
                       invoked. See Issue #372 */
                    form_element.find('input[type=submit][name=_save]').click();

                } else {
                    $("div#popup_bg").remove();
                    form_element.val($(input_element).data('original_value')); // Restore original value
                }
            });

            return false;
        }

        // The template key's widget could either be a radio button or a drop-down select.
        var template_key_radio = $('input[type=radio][name=template_key]');
        template_key_radio.click(on_template_key_changed);
        var template_key_select = $('select[name=template_key]');
        template_key_select.change(on_template_key_changed);

        // Save template key's original value for easy restore if the user cancels the change.
        template_key_radio.data('original_value', template_key_radio.val());
        template_key_select.data('original_value', template_key_select.val());

        $('form').submit(function(){
            give_ordering_to_content_types();
            var form = $(this);
            form.attr('action', form.attr('action')+window.location.hash);
            return true;
        });

        // move contents into their corresponding regions and do some simple formatting
        $("div.feincms_inline div.inline-related").each(function(){
            var elem = $(this);
            if (elem.find("span.delete input").attr("checked")) {
                // ignore all inlines that are set to be deleted by reversion
                return;
            }

            elem.find("input[name$=-region]").addClass("region-choice-field");
            elem.find("input[name$=-DELETE]").addClass("delete-field");
            elem.find("input[name$=-ordering]").addClass("order-field");

            if (!elem.hasClass("empty-form")){
                var region_id = REGION_MAP.indexOf(
                    elem.find(".region-choice-field").val());
                if (REGION_MAP[region_id] != undefined) {
                    var content_type = elem.attr("id").substr(
                        0, elem.attr("id").lastIndexOf("_"));
                    var item = create_new_item_from_form(
                        elem, CONTENT_NAMES[content_type], content_type);
                    add_fieldset(region_id, item, {where:'append'});
                    update_item_controls(item, region_id);
                }
            }
        });
        // register regions as sortable for drag N drop
        $(".order-machine").sortable({
            handle: '.handle',
            helper: function(event, ui){
                var h2 = $("<h2>").html($(ui).find('span.modname').html());
                return $("<fieldset>").addClass("helper module").append(h2);
            },
            placeholder: 'highlight',
            start: function(event, ui) {
                poorify_rich($(ui.item));
            },
            stop: function(event, ui) {
                richify_poor($(ui.item));
            }
        });

        order_content_types_in_regions();

        // hide now-empty formsets
        $('div.feincms_inline').hide();

        // add quick buttons to order machine control
        init_content_type_buttons();

        // DRY object-tools addition
        $(".extra-object-tools li").appendTo("ul.object-tools");
        $(".extra-object-tools").remove();

        /* handle Cmd-S and Cmd-Shift-S as save-and-continue and save respectively */
        $(document.documentElement).keydown(function(event) {
            if(event.which == 83 && event.metaKey) {
                sel = event.shiftKey ? 'form:first input[name=_continue]' :
                    'form:first input[name=_save]';
                $(sel).click();
                return false;
            }
        });


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

    $(window).load(function(){init_contentblocks();});

    // externally accessible helpers
    window.ItemEditor = {
        add_content: function(type, region) {
            var new_fieldset = create_new_fieldset_from_module(type, CONTENT_NAMES[type]);
            add_fieldset(region, new_fieldset, {where: 'append', animate: 'true'});
            update_item_controls(new_fieldset, region);
            return new_fieldset;
        },

        add_content_to_current: function(type) {
            return ItemEditor.add_content(type, ACTIVE_REGION);
        }
    };

})(feincms.jQuery);
