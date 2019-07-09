var PendingApps = (function() {
    var alerts = $('#cy-alerts');
    function setup_accept_and_decline_btns() {
        $('[pending_id]').each(function() {
            var pending_tag = $(this);
            var app_name = $(this).find('.cy-app-name').text();
            var app_version = $(this).find('.cy-app-version').text();
            var pending_id = $(this).attr('pending_id');
            
            function do_action(action, msg, msg_type) {
                pending_tag.find('.btn').hide();
                pending_tag.find('.cy-loading').show();
                $.post('',
                       {'action': action,
                       'pending_id': pending_id},
                       function() {
                            pending_tag.hide('slow', function() {
                                pending_tag.remove();
                            });
                            msg = msg.replace('%s', app_name + ' ' + app_version);
                            var msg_tag = $('<div>').
                                addClass('alert').
                                addClass('alert-' + msg_type).
                                html(msg).
                                prependTo(alerts);
                            msg_tag.hide().slideDown('fast');
                       });
            }
            
            $(this).find('.cy-accept').click(function() {
                do_action('accept', '&ldquo;%s&rdquo; has been accepted.', 'success')
            });
            $(this).find('.cy-decline').click(function() {
                do_action('decline', '&ldquo;%s&rdquo; has been declined.', 'error')
            });
        });
    }
    
    return {
        'setup_accept_and_decline_btns': setup_accept_and_decline_btns,
    };
})();