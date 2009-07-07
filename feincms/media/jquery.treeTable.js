/* jQuery treeTable Plugin 2.2 - http://ludo.cubicphuse.nl/jquery-plugins/treeTable/ */
(function($) {
  // Helps to make options available to all functions
  // TODO: This gives problems when there are both expandable and non-expandable
  // trees on a page. The options shouldn't be global to all these instances!
  var options;

  $.fn.treeTable = function(opts) {
    options = $.extend({}, $.fn.treeTable.defaults, opts);

    return this.each(function() {
      $(this).addClass("treeTable").find("tbody tr").each(function() {
        // Initialize root nodes only whenever possible
        if(!options.expandable || $(this)[0].className.search("child-of-") == -1) {
          initialize($(this));
        }
      });
    });
  };

  $.fn.treeTable.defaults = {
    childPrefix: "child-of-",
    expandable: true,
    indent: 19,
    initialState: "collapsed",
    treeColumn: 0
  };

  // Recursively hide all node's children in a tree
  $.fn.collapse = function() {
    var e0 = $(this);
    e0.addClass("collapsed");

    childrenOf(e0).each(function() {
      var e1 = $(this);
      initialize(e1);

      if(!e1.hasClass("collapsed")) {
        e1.collapse();
      }

      e1.hide();
    });

    return this;
  };

  // Recursively show all node's children in a tree
  $.fn.expand = function() {
    var e0 = $(this);
    e0.removeClass("collapsed").addClass("expanded");

    childrenOf(e0).each(function() {
      var e1 = $(this);
      initialize(e1);

      if(e1.is(".expanded.parent")) {
        e1.expand();
      }

      e1.show();
    });

    return this;
  };

  // Add an entire branch to +destination+
  $.fn.appendBranchTo = function(destination) {
    var node = $(this);
    var parent = parentOf(node);

    var ancestorNames = $.map(ancestorsOf(destination), function(a) { return a.id; });

    // Conditions:
    // 1: +node+ should not be inserted in a location in a branch if this would
    //    result in +node+ being an ancestor of itself.
    // 2: +node+ should not have a parent OR the destination should not be the
    //    same as +node+'s current parent (this last condition prevents +node+
    //    from being moved to the same location where it already is).
    // 3: +node+ should not be inserted as a child of +node+ itself.
    if($.inArray(node[0].id, ancestorNames) == -1 && (!parent || (destination.attr("id") != parent[0].id)) && destination.attr("id") != node[0].id) {
      indent(node, ancestorsOf(node).length * options.indent * -1); // Remove indentation

      if(parent) { node.removeClass(options.childPrefix + parent[0].id); }

      var dest_id = $(destination).attr("id");
      while ($(".child-of-"+dest_id).length > 0) {
          var move_to = $(".child-of-"+dest_id+":last");
          dest_id = move_to.attr("id");
      }

      node.addClass(options.childPrefix + destination.attr("id"));
      if (move_to)
          moveChild(node, move_to); // Recursively move nodes to new location
      else
          moveChild(node, destination);
      indent(node, ancestorsOf(node).length * options.indent);
    }

    return this;
  };

  $.fn.insertBranchBefore = function(destination) {
        var node = $(this);
        var parent = parentOf_jQuery(node);
        var dest_parent = parentOf_jQuery(destination);

        if ($(this).attr("id")==destination.attr("id"))
            return false;

        var ancestorNames = $.map(ancestorsOf_jQuery(destination), function(a) { return a.id; });

        indent(node, ancestorsOf_jQuery(node).length * options.indent * -1); // Remove indentation

        if(parent) { node.removeClass(options.childPrefix + parent[0].id); }

        if (dest_parent)
        node.addClass(options.childPrefix + dest_parent.attr("id"));

        moveBefore(node, destination); // Recursively move nodes to new location
        indent(node, (ancestorsOf_jQuery(node).length * options.indent));

        return this;
  };

  // Add reverse() function from JS Arrays
  $.fn.reverse = function() {
    return this.pushStack(this.get().reverse(), arguments);
  };

  // Toggle an entire branch
  $.fn.toggleBranch = function() {
    var e0 = $(this);

    if(e0.hasClass("collapsed")) {
      e0.expand();
    } else {
      e0.removeClass("expanded").collapse();
    }

    return this;
  };

  // === Private functions

  function ancestorsOf(node) {
    var ancestors = [];
    while(node = parentOf(node)) {
      ancestors[ancestors.length] = node[0];
    }
    return ancestors;
  };

  function childrenOf(node) {
    return $("table.treeTable tbody tr." + options.childPrefix + node[0].id);
  };

  function indent(node, value) {
    var cell = $(node.children("td")[options.treeColumn]);
    var padding = parseInt(cell.css("padding-left"), 10) + value;

    cell.css("padding-left", + padding + "px");

    childrenOf(node).each(function() {
      indent($(this), value);
    });
  };

  function initialize(node) {
    if(!node.hasClass("initialized")) {
      node.addClass("initialized");

      var childNodes = childrenOf(node);

      if(!node.hasClass("parent") && childNodes.length > 0) {
        node.addClass("parent");
      }

      if(node.hasClass("parent")) {
        var cell = $(node.children("td")[options.treeColumn]);
        var padding = parseInt(cell.css("padding-left"), 10) + options.indent;

        childNodes.each(function() {
          $($(this).children("td")[options.treeColumn]).css("padding-left", padding + "px");
        });

        if(options.expandable) {
            cell.children(":first").children("span").prepend('<span style="margin-left: -' + (options.indent-15) + 'px; padding-left: ' + (options.indent-3) + 'px;" class="expander"></span>');
          //$(cell[0].firstChild).click(function() { node.toggleBranch(); });

          // Check for a class set explicitly by the user, otherwise set the default class
          if(!(node.hasClass("expanded") || node.hasClass("collapsed"))) {
            node.addClass(options.initialState);
          }

          if(node.hasClass("collapsed")) {
            node.collapse();
          } else if (node.hasClass("expanded")) {
            node.expand();
          }
        }
      } else {
          var cell = $(node.children("td")[options.treeColumn]);
          cell.children(":first").children("span").prepend('<span style="margin-left: -' + (options.indent-15) + 'px; padding-left: ' + (options.indent-3) + 'px;"></span>');
      }
      node.children(":first").addClass("padded");
    }
  };

  function move(node, destination) {
    node.insertAfter(destination);
    childrenOf(node).reverse().each(function() { move($(this), node[0]); });
  };

  function moveChild(node, destination) {
    node.insertAfter(destination)
    childrenOf(node).reverse().each(function() { move($(this), node[0]); });

  };

  function moveBefore(node, destination) {
    node.insertBefore(destination)
    childrenOf(node).reverse().each(function() { move($(this), node[0]); });
  };

  function parentOf(node) {

    var classNames = node[0].className.split(' ');

    for(key in classNames) {
      if(classNames[key].match("child-of-")) {
        return $("#" + classNames[key].substring(9));
      }
    }
  };
})(jQuery);

// public functions
function handle_drop_event(source, dest, method){
    var ancestorNames = $.map(ancestorsOf_jQuery(dest), function(a) { return a.attr("id"); });
    if (method=="child")
        dest.find(".wrap").removeClass("hover-as-child").addClass("nohover");
    else
        dest.find('.wrap').removeClass('hover-as-sibling').addClass('nohover');

    // do not drop on itself or its own children, if method == "child"
    if ( (method == "sibling") || (source.attr("id") != dest.attr("id") && $.inArray(source.attr("id"), ancestorNames) == -1) ) {
        var source_child_of = null;
        if (source.attr("class").match(/child-of-node-(\d+)/))
            source_child_of = source.attr("class").match(/child-of-node-(\d+)/)[0];
        var dest_child_of = "child-of-" + dest.attr("id");
        if (source_child_of && $("."+source_child_of).length - 1 == 0) {
            var parent_id = "#" + source_child_of.substring(9);
            $(parent_id).removeClass("parent");
            if ($(parent_id).hasClass("expanded"))
                $(parent_id).removeClass("expanded").addClass("collapsed");
            $(parent_id+" .title-col span").removeClass("expander");
        }
        if (method=="child") {
            if ($("."+dest_child_of).length == 0) {
                var parent_id = "#" + dest_child_of.substring(9);
                $(parent_id).addClass("parent").find(".title-col span").addClass("expander");
            }
            if (!dest.hasClass("expanded"))
                dest.expand();
            // *** INSERT ***
            source.appendBranchTo(dest);
        } else // method == "sibling"
            source.insertBranchBefore(dest);
    }
    source.find(".wrap").switchClass("nohover","flash",0).switchClass("flash","nohover",500);
    dest.find(".wrap").switchClass("nohover","flash",0).switchClass("flash","nohover",500);

}

function handle_page_delete(node) {
    var item_id = node.attr("class").match(/item-id-(\d+)/)[1];
    var parent_id = null;
    if (node.attr("class").match(/child-of-node-(\d+)/))
        parent_id = node.attr("class").match(/child-of-node-(\d+)/)[1];
    var popup_bg = '<div class="popup_bg"></div>';
    $("body").append(popup_bg);
    if (node.hasClass("parent")){
        jAlert(DELETE_MESSAGES[4], DELETE_MESSAGES[3], function(){
            $(".popup_bg").remove();
        });
    } else {
        jConfirm(DELETE_MESSAGES[0], DELETE_MESSAGES[1], function(r) {
            if (r==true) {
                $.post('.', {'__cmd': 'delete_item', 'item_id': item_id}, function(data){
                    if (data == "OK") {
                        if (parent_id && $(".child-of-node-"+parent_id).length == 1) {
                            $("#node-"+parent_id).removeClass("parent")
                                .removeClass("expanded").addClass("collapsed")
                                .find(".expander").removeClass("expander");
                        }
                        node.remove();
                        $("body").append(popup_bg);
                        jAlert(DELETE_MESSAGES[2], DELETE_MESSAGES[2], function(){
                                $(".popup_bg").remove();
                        });
                    }
                });
            }
            $(".popup_bg").remove();
        });
    }
}

function parentOf_jQuery(node) {
    if (node.attr("class").match(/child-of-node-(\d+)/)) {
        var parent_id = node.attr("class").match(/child-of-node-(\d+)/)[1];
        return $("#node-"+parent_id);
    }
    return null;
};

function ancestorsOf_jQuery(node) {
    var ancestors = [];
    while(node = parentOf_jQuery(node)) {
      ancestors[ancestors.length] = node;
    }
    return ancestors;
};

function save_page_tree() {
    var send_tree = new Array();

   // prepare tree
    var i = 0;
    var ancestor_tree_ids = [];
    var ancestor_indices = [];
    var tree_id = 0;
    $("#sitetree tbody tr").each(function(){
        // 0 = tree_id, 1 = parent_id, 2 = left, 3 = right, 4 = level, 5 = item_id
        var classNames = $(this).attr("class").split(' ');
        var is_child = false;
        var is_parent = false;
        var parent_id = null;
        var item_id = "";
        var left = "";
        var right = "";
        var level = "";

        // gather information
        for (key in classNames) {
            if(classNames[key].match("item-id-"))
                item_id = parseInt(classNames[key].substring(8));
            if(classNames[key].match("parent"))
                is_parent = true;
            if(classNames[key].match("child-of-")) {
                is_child = true;
                var node_parent_id = classNames[key].substring(9);
                parent_id = parseInt($("#"+node_parent_id).attr("class").match(/item-id-(\d+)/)[1])
            }
        }
        // save info
        var inArray = ancestor_tree_ids.indexOf(parent_id);

        while (
                ( is_child && inArray < ancestor_tree_ids.length - 1 && inArray >= 0)
                    // We are working on a child currently (not a root node).
                    // Walk back up the tree until the last entries in the ancestor
                    // arrays belong to the parent of the current item. We can then
                    // proceed by filling in the left value for the current entry.
                || ( !is_child && ancestor_tree_ids.length > 0 )
                    // We are working on a new root node. Completely drain the ancestor
                    // arrays and proceed by opening a new tree (see next if statement).
                ) {
            send_tree[ancestor_indices.pop()][3] = i++;
            ancestor_tree_ids.pop();
        }
        if (!is_child) {
            // Start with the next tree, reset left/right value
            tree_id++;
            i = 0;
        }
        left = i++;
        level = ancestor_tree_ids.length;
        if (is_parent) {
            // Walk down the tree -- the current entry is the parent of the next entry.
            ancestor_tree_ids.push(item_id);
            ancestor_indices.push(send_tree.length);
        } else {
            // No children -- fill in right value now
            right = i++;
        }

        send_tree.push([tree_id, parent_id?parent_id:null, left, right, level, item_id]);
    });

    // Drain the ancestor array again
    while (ancestor_tree_ids.length>0) {
        send_tree[ancestor_indices.pop()][3] = i++;
        ancestor_tree_ids.pop();
    }

    // send tree to url
    $.post('.', {'__cmd': 'save_tree', 'tree': $.toJSON(send_tree)}, function(data){
        if (data == "OK") {
            var popup_bg = '<div class="popup_bg"></div>';
            $("body").append(popup_bg);
            jAlert(TREE_SAVED_MESSAGE, TREE_SAVED_MESSAGE, function(){
                $(".popup_bg").remove();
            });
        }
    });
}
