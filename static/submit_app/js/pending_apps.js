var PendingApps = (function() {
    var alerts = $('#cy-alerts');
    function setup_accept_and_decline_btns() {
        $('[pending_id]').each(function() {
            var pending_tag = $(this);
            var app_name = $(this).find('.cy-app-name, .cy-service-app-name, .cy-web-app-name, .cy-pending-name, .cy-pending-title').first().text().trim();
            var app_version = $(this).find('.cy-app-version, .cy-service-app-version, .cy-pending-version, .cy-web-app-version').first().text().trim();
            var app_version = $(this).find('.cy-app-version').text();
            var pending_id = $(this).attr('pending_id');
            var pending_platform = $(this).attr('pending_platform')
            
            function do_action(action, msg, msg_type) {
                pending_tag.find('.btn').hide();
                pending_tag.find('.cy-loading').show();
                $.post('',
                       {'action': action,
                       'pending_id': pending_id,
                        'pending_platform': pending_platform},
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
            $(this).find('.cy-try-web').click(function(e) {
                e.preventDefault()
                var endpoint = $(this).data('service_endpoint') || $(this).data('endpoint') || '';
                if(!endpoint) {
                    alert('No service endpoint available for this pending item.');
                    return;
                }
                var base=window.CYTOSCAPE_WEB_BASE || "https://web.cytoscape.org"
                var url = base + (base.indexOf('?') === -1 ? '?service_url=' : '&service_url=') + encodeURIComponent(endpoint);
                window.open(url, '_blank', 'noopener');
            })
        });
    }
    
    return {
        'setup_accept_and_decline_btns': setup_accept_and_decline_btns,
    };
})();