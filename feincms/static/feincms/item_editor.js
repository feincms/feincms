/* global Downcoder, django, feincms, ItemEditor, interpolate */
/* global IMG_DELETELINK_PATH, REGION_MAP, REGION_NAMES, CONTENT_NAMES, FEINCMS_ITEM_EDITOR_GETTEXT, CONTENT_TYPE_BUTTONS */
/* global contentblock_init_handlers, contentblock_move_handlers */
/* global id_to_windowname */
/* global template_regions */

// IE<9 lacks Array.prototype.indexOf
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function (needle) {
    for (let i = 0, l = this.length; i < l; ++i) {
      if (this[i] === needle) return i
    }
    return -1
  }
}

;(function ($) {
  // Patch up urlify maps to generate nicer slugs in german
  if (typeof Downcoder != "undefined") {
    Downcoder.Initialize()
    Downcoder.map["ö"] = Downcoder.map["Ö"] = "oe"
    Downcoder.map["ä"] = Downcoder.map["Ä"] = "ae"
    Downcoder.map["ü"] = Downcoder.map["Ü"] = "ue"
  }

  function feincms_gettext(s) {
    // Unfortunately, we cannot use Django's jsi18n view for this
    // because it only sends translations from the package
    // "django.conf" -- our own djangojs domain strings won't be
    // picked up

    if (FEINCMS_ITEM_EDITOR_GETTEXT[s]) return FEINCMS_ITEM_EDITOR_GETTEXT[s]
    return s
  }

  function create_new_item_from_form(form, modname, modvar) {
    let fieldset = $("<fieldset>").addClass(
      `module aligned order-item item-wrapper-${modvar}`
    )
    let original_id_id = `#id_${form.attr("id")}-id`

    let wrp = ["<h2>"]
    // If original has delete checkbox or this is a freshly added CT? Add delete link!
    if ($(".delete", form).length || !$(original_id_id, form).val()) {
      wrp.push(`<img class="item-delete" src="${IMG_DELETELINK_PATH}" />`)
    }
    wrp.push(
      `<span class="handle"></span> <span class="modname">${modname}</span></h2>`
    )
    wrp.push('<div class="item-content"></div>')
    fieldset.append(wrp.join(""))

    fieldset.children(".item-content").append(form) //relocates, not clone

    $("<div>").addClass("item-controls").appendTo(fieldset)

    return fieldset
  }

  const SELECTS = {}
  function save_content_type_selects() {
    $("#feincmsmain>.panel").each(function () {
      SELECTS[this.id.replace(/_body$/, "")] = $(
        "select[name=order-machine-add-select]",
        this
      )
        .clone()
        .removeAttr("name")
    })
  }

  function update_item_controls(item, target_region_id) {
    let item_controls = item.find(".item-controls")
    item_controls.empty()

    // Insert control unit
    let insert_control = $("<div>").addClass("item-control-unit")
    let select_content = SELECTS[REGION_MAP[target_region_id]].clone()

    select_content.change(() => {
      let modvar = select_content.val()
      let modname = select_content.find("option:selected").html()
      let new_fieldset = create_new_fieldset_from_module(modvar, modname)
      add_fieldset(target_region_id, new_fieldset, {
        where: "insertBefore",
        relative_to: item,
        animate: true,
      })
      update_item_controls(new_fieldset, target_region_id)

      select_content.val("")
    })
    insert_control.append(select_content)
    item_controls.append(insert_control)

    // Move control unit
    if (REGION_MAP.length > 1) {
      let wrp = []
      wrp.push(
        '<div class="item-control-unit move-control"><select name="item-move-select">'
      )
      wrp.push(
        `<option disabled selected>${feincms_gettext(
          "MOVE_TO_REGION"
        )}</option>`
      )

      for (let i = 0; i < REGION_MAP.length; i++) {
        if (i != target_region_id) {
          // Do not put the target region in the list
          wrp.push(
            `<option value="${REGION_MAP[i]}">${REGION_NAMES[i]}</option>`
          )
        }
      }
      wrp.push("</select>")

      let move_control = $(wrp.join(""))
      move_control.find("select").change(function () {
        let move_to = $(this).val()
        move_item(REGION_MAP.indexOf(move_to), item)
      })
      item_controls.append(move_control) // Add new one
    }
  }

  function create_new_fieldset_from_module(modvar, modname) {
    let new_form = create_new_spare_form(modvar)
    return create_new_item_from_form(new_form, modname, modvar)
  }

  function add_fieldset(region_id, item, how) {
    /* `how` should be an object.
           `how.where` should be one of:
         - 'append' -- last region
         - 'prepend' -- first region
         - 'insertBefore' -- insert before relative_to
         - 'insertAfter' -- insert after relative_to */

    // Default parameters
    if (how)
      $.extend(
        {
          where: "append",
          relative_to: undefined,
          animate: false,
        },
        how
      )

    item.hide()
    if (how.where == "append" || how.where == "prepend") {
      $(`#${REGION_MAP[region_id]}_body`)
        .children("div.order-machine")
        [how.where](item)
    } else if (how.where == "insertBefore" || how.where == "insertAfter") {
      if (how.relative_to) {
        item[how.where](how.relative_to)
      } else {
        window.alert("DEBUG: invalid add_fieldset usage")
        return
      }
    } else {
      window.alert("DEBUG: invalid add_fieldset usage")
      return
    }
    set_item_field_value(item, "region-choice-field", region_id)
    init_contentblocks()

    if (how.animate) {
      item.fadeIn(800)
    } else {
      item.show()
    }
  }

  function create_new_spare_form(modvar) {
    let old_form_count = parseInt($(`#id_${modvar}_set-TOTAL_FORMS`).val(), 10)
    // **** UGLY CODE WARNING, avert your gaze! ****
    // for some unknown reason, the add-button click handler function
    // fails on the first triggerHandler call in some rare cases;
    // we can detect this here and retry:
    for (let i = 0; i < 2; i++) {
      // Use Django's built-in inline spawing mechanism (Django 1.2+)
      // must use django.jQuery since the bound function lives there:
      django
        .jQuery(`#${modvar}_set-group`)
        .find(".add-row a")
        .triggerHandler("click")
      let new_form_count = parseInt(
        $(`#id_${modvar}_set-TOTAL_FORMS`).val(),
        10
      )
      if (new_form_count > old_form_count) {
        return $(`#${modvar}_set-${new_form_count - 1}`)
      }
    }
  }

  function set_item_field_value(item, field, value) {
    // item: DOM object for the item's fieldset.
    // field: "order-field" | "delete-field" | "region-choice-field"
    if (field == "delete-field") item.find(`.${field}`).attr("checked", value)
    else if (field == "region-choice-field") {
      let old_region_id = REGION_MAP.indexOf(item.find(`.${field}`).val())
      item.find(`.${field}`).val(REGION_MAP[value])

      // show/hide the empty machine message in the source and
      // target region.
      let old_region_item = $(`#${REGION_MAP[old_region_id]}_body`)
      if (old_region_item.children("div.order-machine").children().length == 0)
        old_region_item.children("div.empty-machine-msg").show()
      else old_region_item.children("div.empty-machine-msg").hide()

      let new_region_item = $(`#${REGION_MAP[value]}_body`)
      new_region_item.children("div.empty-machine-msg").hide()
    } else item.find(`.${field}`).val(value)
  }

  function move_item(region_id, item) {
    poorify_rich(item)
    item.fadeOut(800, () => {
      add_fieldset(region_id, item, { where: "append" })
      richify_poor(item)
      update_item_controls(item, region_id)
      item.show()
    })
  }

  function poorify_rich(item) {
    item.children(".item-content").hide()

    for (let i = 0; i < contentblock_move_handlers.poorify.length; i++)
      contentblock_move_handlers.poorify[i](item)
  }

  function richify_poor(item) {
    item.children(".item-content").show()

    for (let i = 0; i < contentblock_move_handlers.richify.length; i++)
      contentblock_move_handlers.richify[i](item)
  }

  function sort_by_ordering(e1, e2) {
    let v1 = parseInt($(".order-field", e1).val(), 10) || 0
    let v2 = parseInt($(".order-field", e2).val(), 10) || 0
    return v1 > v2 ? 1 : -1
  }

  function give_ordering_to_content_types() {
    for (let i = 0; i < REGION_MAP.length; i++) {
      let container = $(`#${REGION_MAP[i]}_body div.order-machine`)
      for (let j = 0; j < container.children().length; j++) {
        set_item_field_value(
          container.find(`fieldset.order-item:eq(${j})`),
          "order-field",
          j
        )
      }
    }
  }

  function order_content_types_in_regions() {
    for (let i = 0; i < REGION_MAP.length; i++) {
      let container = $(`#${REGION_MAP[i]}_body div.order-machine`)
      container
        .children()
        .sort(sort_by_ordering)
        .each(function () {
          container.append(this)
        })
    }
  }

  function init_contentblocks() {
    for (let i = 0; i < contentblock_init_handlers.length; i++)
      contentblock_init_handlers[i]()
  }

  function hide_form_rows_with_hidden_widgets() {
    /* This is not normally done in django -- the fields are shown
           with visible labels and invisible widgets, but FeinCMS used to
           use custom form rendering to hide rows for hidden fields.
           This is an attempt to preserve that behaviour. */
    $("div.feincms_inline div.form-row").each(function () {
      let child_count = $(this).find("*").length
      let invisible_types = "div, label, input[type=hidden], p.help"
      let invisible_count = $(this).find(invisible_types).length
      if (invisible_count == child_count) {
        $(this).addClass("hidden-form-row")
      }
    })
  }

  function init_content_type_buttons() {
    $("#feincmsmain > .panel").each(function () {
      let $select = $("select[name=order-machine-add-select]", this),
        to_remove = []

      $select.change(() => {
        let modvar = $select.val()
        // bail out early if no content type selected
        if (!modvar) return

        let modname = $select.find("option:selected").html()
        let new_fieldset = create_new_fieldset_from_module(modvar, modname)
        add_fieldset(window.ACTIVE_REGION, new_fieldset, {
          where: "append",
          animate: true,
        })
        update_item_controls(new_fieldset, window.ACTIVE_REGION)

        $select.val("")
      })

      for (let i = 0; i < CONTENT_TYPE_BUTTONS.length; i++) {
        let c = CONTENT_TYPE_BUTTONS[i],
          $option = $select.find(`option[value=${c.type}]`)

        if (!$option.length) continue

        let $button = $('<a href="#" class="actionbutton" />')
        $button.attr("title", CONTENT_NAMES[c.type])

        $button.addClass(c.cssclass ? c.cssclass : c.type).bind(
          "click",
          (function (c) {
            return function () {
              let fieldset = ItemEditor.add_content_to_current(c.type)
              if (c.raw_id_picker) {
                let id = fieldset
                  .find(".related-lookup, span.mediafile")
                  .attr("id")

                if (id) {
                  window
                    .open(
                      c.raw_id_picker,
                      id_to_windowname(id.replace(/^lookup_/, "")),
                      "height=500,width=800,resizable=yes,scrollbars=yes"
                    )
                    .focus()
                }
              }
              if (c.after) c.after.call(null, fieldset)
              return false
            }
          })(c)
        )

        $select.parent().append($button)

        if (!c.keep) to_remove.push($option)
      }

      for (let i = 0; i < to_remove.length; i++) to_remove[i].remove()

      if ($select.find("option").length == 0) {
        // hide the content type select box and the add button if
        // the dropdown is empty now
        $select.hide().next().hide()
      }
    })
  }

  function create_tabbed(_tab_selector, _main_selector, _switch_cb) {
    let tab_selector = _tab_selector,
      main_selector = _main_selector,
      switch_cb = _switch_cb

    $(tab_selector).addClass("clearfix")

    $(`${tab_selector} > .navi_tab`).on("click", function () {
      let elem = $(this),
        tab_str = elem.attr("id").substr(0, elem.attr("id").length - 4)

      if (
        elem.hasClass("tab_active") &&
        tab_str.indexOf("extension_option") != -1
      ) {
        elem.removeClass("tab_active")
        $(`#${tab_str}_body`).hide()
      } else {
        $(`${tab_selector} > .navi_tab`).removeClass("tab_active")
        elem.addClass("tab_active")
        $(
          `${main_selector} > div:visible, ${main_selector} > fieldset:visible`
        ).hide()

        $(`#${tab_str}_body`).show()

        if (switch_cb) {
          switch_cb(tab_str)
        }
      }
    })
  }

  // global variable holding the current template key
  let current_template

  $(document).ready(($) => {
    hide_form_rows_with_hidden_widgets()

    create_tabbed("#feincmsmain_wrapper", "#feincmsmain", (tab_str) => {
      window.ACTIVE_REGION = REGION_MAP.indexOf(tab_str)
      // make it possible to open current tab on page reload
      window.location.replace(`#tab_${tab_str}`)
    })

    /* Rearrange the options fieldsets so we can wrap them into a tab bar */
    let options_fieldsets = $("fieldset.collapse")
    options_fieldsets.wrapAll('<div id="extension_options_wrapper" />')
    let option_wrapper = $("#extension_options_wrapper")
    let panels = []

    options_fieldsets.each((idx, elem) => {
      let option_title = $("h2", $(elem)).text()
      let id_base = `extension_option_${idx}`

      let paren = option_title.indexOf(" (")
      if (paren > 0) option_title = option_title.substr(0, paren)

      option_wrapper.append(
        `<div class="navi_tab" id="${id_base}_tab">${option_title}</div>`
      )
      let panel = $(
        `<fieldset class="module aligned" style="clear: both; display: none" id="${id_base}_body"></fieldset>`
      )
      let $elem = $(elem)
      panel.append($elem.children("div"))
      $elem.remove() // Remove the rest
      panels.push(panel)
    })

    option_wrapper.append('<div id="extension_options" />')
    $("#extension_options").append(panels)

    create_tabbed("#extension_options_wrapper", "#extension_options")
    /* Done morphing extension options into tabs */

    // save content type selects for later use
    save_content_type_selects()

    $(document.body).on("click", "h2 img.item-delete", function () {
      let item = $(this).parents(".order-item")
      if (confirm(feincms_gettext("DELETE_MESSAGE"))) {
        let in_database = item.find(".delete-field").length
        if (in_database == 0) {
          // remove on client-side only
          let id = item.find(".item-content > div").attr("id")

          // poorify all contents
          let items = item.parents(".order-machine").find(".order-item")
          items.each(function () {
            poorify_rich($(this))
          })

          // remove content
          django
            .jQuery(`#${id}`)
            .find("a.inline-deletelink")
            .triggerHandler("click")

          // richify all contents again
          items.each(function () {
            richify_poor($(this))
          })
        } else {
          // saved on server, don't remove form
          set_item_field_value(item, "delete-field", "checked")
        }
        item.fadeOut(200, () => {
          let region_item = $(`#${REGION_MAP[window.ACTIVE_REGION]}_body`)
          if (
            region_item.children("div.order-machine").children(":visible")
              .length == 0
          ) {
            region_item.children("div.empty-machine-msg").show()
          }
        })
      }
    })

    current_template = $(
      "input[name=template_key][checked], select[name=template_key]"
    ).val()

    function on_template_key_changed() {
      let input_element = this
      let new_template = this.value
      let form_element = $(input_element).parents("form")

      if (current_template == new_template)
        // Selected template did not change
        return false

      let current_regions = template_regions[current_template]
      let new_regions = template_regions[new_template]

      let not_in_new = []
      for (let i = 0; i < current_regions.length; i++)
        if (new_regions.indexOf(current_regions[i]) == -1)
          not_in_new.push(current_regions[i])

      let msg = feincms_gettext("CHANGE_TEMPLATE")

      if (not_in_new.length) {
        msg = interpolate(
          feincms_gettext("CHANGE_TEMPLATE_WITH_MOVE"),
          {
            source_regions: not_in_new,
            target_region: new_regions[0],
          },
          true
        )
      }

      if (confirm(msg)) {
        for (let i = 0; i < not_in_new.length; i++) {
          let body = $(`#${not_in_new[i]}_body`),
            machine = body.find(".order-machine"),
            inputs = machine.find("input[name$=region]")

          inputs.val(new_regions[0])
        }

        input_element.checked = true

        form_element.append(
          '<input type="hidden" name="_continue" value="1" />'
        )
        /* Simulate a click on the save button instead of form.submit(), so
                   that the submit handlers from FilteredSelectMultiple get
                   invoked. See Issue #372 */
        form_element.find("[type=submit][name=_save]").click()
      } else {
        // Restore original value
        form_element.val($(input_element).data("original_value"))
      }

      return false
    }

    // The template key's widget could either be a radio button or a drop-down select.
    let template_key_radio = $("input[type=radio][name=template_key]")
    template_key_radio.click(on_template_key_changed)
    let template_key_select = $("select[name=template_key]")
    template_key_select.change(on_template_key_changed)

    // Save template key's original value for easy restore if the user cancels the change.
    template_key_radio.data("original_value", template_key_radio.val())
    template_key_select.data("original_value", template_key_select.val())

    $("form").submit(function () {
      give_ordering_to_content_types()
      let form = $(this)
      let action = form.attr("action") || ""
      form.attr("action", action + window.location.hash)
      return true
    })

    // move contents into their corresponding regions and do some simple formatting
    $("div.feincms_inline div.inline-related").each(function () {
      let elem = $(this)
      if (elem.find("span.delete input").attr("checked")) {
        // ignore all inlines that are set to be deleted by reversion
        return
      }

      elem.find("input[name$=-region]").addClass("region-choice-field")
      elem.find("input[name$=-DELETE]").addClass("delete-field")
      elem.find("input[name$=-ordering]").addClass("order-field")

      if (!elem.hasClass("empty-form")) {
        let region_id = REGION_MAP.indexOf(
          elem.find(".region-choice-field").val()
        )
        if (REGION_MAP[region_id] != undefined) {
          let content_type = elem
            .attr("id")
            .substr(0, elem.attr("id").lastIndexOf("_"))
          let item = create_new_item_from_form(
            elem,
            CONTENT_NAMES[content_type],
            content_type
          )
          add_fieldset(region_id, item, { where: "append" })
          update_item_controls(item, region_id)
        }
      }
    })
    // register regions as sortable for drag N drop
    $(".order-machine").sortable({
      handle: ".handle",
      helper(event, ui) {
        let h2 = $("<h2>").html($(ui).find("span.modname").html())
        return $("<fieldset>").addClass("helper module").append(h2)
      },
      placeholder: "highlight",
      start(event, ui) {
        poorify_rich($(ui.item))
      },
      stop(event, ui) {
        richify_poor($(ui.item))
      },
    })

    order_content_types_in_regions()

    // hide now-empty formsets
    $("div.feincms_inline").hide()

    // add quick buttons to order machine control
    init_content_type_buttons()

    // DRY object-tools addition
    $(".extra-object-tools li").appendTo("ul.object-tools")
    $(".extra-object-tools").remove()

    /* handle Cmd-S and Cmd-Shift-S as save-and-continue and save respectively */
    $(document.documentElement).keydown((event) => {
      if (event.which == 83 && event.metaKey) {
        let sel = event.shiftKey
          ? "form:first input[name=_continue]"
          : "form:first input[name=_save]"
        $(sel).click()
        return false
      }
    })

    let errors = $("#feincmsmain div.errors")

    if (errors.length) {
      let id = errors.parents("fieldset[id$=_body], div[id$=_body]").attr("id")
      $(`#${id.replace("_body", "_tab")}`).trigger("click")
    } else {
      if (window.location.hash) {
        let tab = $(`#${window.location.hash.substr(5)}_tab`)

        if (tab.length) {
          tab.trigger("click")
          return
        }
      }

      $("#feincmsmain_wrapper>div.navi_tab:first-child").trigger("click")
    }
  })

  $(window).load(init_contentblocks)

  // externally accessible helpers
  window.ItemEditor = {
    add_content(type, region) {
      let new_fieldset = create_new_fieldset_from_module(
        type,
        CONTENT_NAMES[type]
      )
      add_fieldset(region, new_fieldset, { where: "append", animate: "true" })
      update_item_controls(new_fieldset, region)
      return new_fieldset
    },

    add_content_to_current(type) {
      return ItemEditor.add_content(type, window.ACTIVE_REGION)
    },
  }
})(feincms.jQuery)
