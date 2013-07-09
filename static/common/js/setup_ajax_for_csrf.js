(function() {
    $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
            }
    });
})();