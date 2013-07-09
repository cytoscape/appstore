var SortAppButtons = (function() {
    var descending = false;
    var prev_sort_by = null;
    
    var sort_funcs = {
      'int': function(attr_name) {
            return function(a, b) {
                var numA = parseInt(a.attr(attr_name));
                var numB = parseInt(b.attr(attr_name));
                return numA - numB;
            };
        },
        
        'str': function(attr_name) {
            return function(a, b) {
                var nameA = a.attr(attr_name).toLowerCase();
                var nameB = b.attr(attr_name).toLowerCase();
                if (nameA > nameB)
                    return 1;
                else if (nameB > nameA)
                    return -1;
                else
                    return 0;
            }
        }
    };
    
    
    function sort_app_buttons(container, sort_func) {
        var lpanel = container.find('#left');
        var rpanel = container.find('#right');
        
        var buttons = [];
        container.find('.app_button').each(function () {
            buttons.push($(this));
        });
        
        buttons.sort(sort_func);
        if (descending)
            buttons = buttons.reverse();
        
        lpanel.empty();
        rpanel.empty();
        
        $.each(buttons, function(index, button) {
            panel = (index % 2 == 0 ? lpanel : rpanel);
            panel.append(button);
        });
    }
    
    function sort_button_by_name(container, name) {
        return container.find('#sort_app_buttons button .title:contains(' + name + ')').parent();
    }
    
    var SORT_BY_COOKIE = 'cytoscape.AppStore.AppButtons.SortBy';
    var SORT_DESCENDING_COOKIE = 'cytoscape.AppStore.AppButtons.SortDescending';

    function setup_sort_buttons(container) {
        var buttons = container.find('#sort_app_buttons');
        buttons.find('button').click(function() {
            var sort_by = $(this).find('.title').text();
            var attr_name = $(this).attr('attr_name');
            var attr_type = $(this).attr('attr_type');
            var sort_func = sort_funcs[attr_type](attr_name);

            if (sort_by === prev_sort_by) {
                descending = !descending;
            } else {
                buttons.find('button .triangle').html('');
                prev_sort_by = sort_by;
                descending = (attr_type === 'int');
            }

            if (!$(this).hasClass('active')) {
                buttons.find('button').removeClass('active');
                $(this).addClass('active');
            }

            $(this).find('.triangle').html(descending ? '&#x25BC;' : '&#x25B2;');
            sort_app_buttons(container, sort_func);

            $.cookie(SORT_BY_COOKIE, sort_by, {path: '/'});
            $.cookie(SORT_DESCENDING_COOKIE, descending, {path: '/'});
        });
    }
   

   return {
       'init_sort_buttons': function(container) {
            setup_sort_buttons(container);
            var sort_by = $.cookie(SORT_BY_COOKIE);
            var sort_button = sort_button_by_name(container, sort_by);
            if (sort_button.length === 0) {
               sort_button_by_name(container, 'name').click();
            } else {
               descending = ($.cookie(SORT_DESCENDING_COOKIE) === 'false');
               prev_sort_by = sort_by;
               sort_button.click();
            }
       }
   };
})();
