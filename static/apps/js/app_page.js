var AppPage = (function($) {
    /*
     ================================================================
       Install via Cytoscape 3 App Manager
     ================================================================
        */

    var AppManagerURL = 'http://127.0.0.1:1234/v1';

    function setup_url_copy() {
        $('.cy-app-url-copy').each(function() {
            var field = this.querySelector('input');
            var button = this.querySelector('button');
            var status = this.querySelector('[role="status"]');

            function select_url() {
                field.focus();
                field.select();
            }

            function manual_copy() {
                select_url();
                status.textContent = 'Press Ctrl+C (Windows/Linux) or Command+C (Mac) to copy the URL.';
                button.disabled = false;
            }

            function copied() {
                status.textContent = 'URL copied!';
                button.disabled = false;
                button.focus();
            }

            function fallback_copy() {
                // The Clipboard API is unavailable on HTTP and may be denied
                // by browser permissions. Try copying the selected field too.
                select_url();
                try {
                    if (document.execCommand('copy')) {
                        copied();
                        return;
                    }
                } catch (error) {
                    // Keep the URL selected if both clipboard methods fail.
                }
                manual_copy();
            }

            field.addEventListener('focus', function() { field.select(); });
            field.addEventListener('click', function() { field.select(); });
            button.hidden = false;
            status.textContent = '';
            button.addEventListener('click', function() {
                if (!navigator.clipboard || !navigator.clipboard.writeText) {
                    fallback_copy();
                    return;
                }
                button.disabled = true;
                status.textContent = 'Copying URL…';
                try {
                    navigator.clipboard.writeText(field.value).then(copied, fallback_copy);
                } catch (error) {
                    fallback_copy();
                }
            });
        });
    }

    function is_manager_running(callback) {
        $.ajax(AppManagerURL, {
            'type': 'GET',
            'success': function() {
                callback(true);
            },
            'error': function() {
                callback(false);
            }
        });
    }

    function get_app_status(fullname, callback) {
           $.ajax(AppManagerURL + '/commands/apps/list%20installed', {
                   'type': 'GET',
                   'success': function(result) {
                       if (result.includes(fullname)) {
                           callback(true);
                       } else {
                           callback(false);
                       }
                   },
                   'error': function() {
                       callback(false);
                   }
               },
               callback);
       }

    function get_app_updates(fullname, callback) {
        $.ajax(AppManagerURL + '/commands/apps/list%20updates', {
                'type': 'GET',
                'success': function(result) {
                    if (result.includes(fullname)) {
                        callback(true);
                    } else {
                        callback(false);
                    }
                },
                'error': function() {
                    callback(false);
                }
            },
            callback);
    }

    function install_app(app_name, app_version, callback) {
        $.ajax(AppManagerURL + '/commands/apps/install?app=' + app_name, {
                'type': 'GET',
                'success': function(result) {
                    if (result.includes('installed')) {
                        callback(true);
                    } else {
                        callback(false);
                    }
                },
                'error': function() {
                    callback(false);
                }
            },
            callback);
    }

    var install_btn = $('#cy-app-install-btn');
    var install_btn_last_class = [];

    function setup_install_btn(btn_class, icon_class, btn_text, func) {
        if (install_btn_last_class.length !== 0)
            install_btn.removeClass(install_btn_last_class.pop());
        install_btn.addClass(btn_class);
        install_btn_last_class.push(btn_class);
    
        install_btn.find('i').attr('class', '');
        install_btn.find('i').addClass(icon_class);
    
        install_btn.find('h4').html(btn_text);
    
        install_btn.off('click');
        install_btn.removeClass('disabled');
    
        if (func) {
            var license_modal = $('#license_modal');
            if (license_modal.length !== 0) {
                // Unbind previous click handlers to prevent double binding
                license_modal.find('.btn-primary').off('click');
    
                license_modal.find('.btn-primary').click(function() {
                    license_modal.modal('hide');
                    func();
                });
    
                install_btn.click(function() {
                    var license_iframe = license_modal.find('iframe');
                    license_iframe.attr('src', license_iframe.attr('data-src'));
                    license_modal.modal('show');
                });
            } else {
                // If license modal doesn't exist in DOM
                install_btn.click(func);
            }
        } else {
            install_btn.addClass('disabled');
        }
    }
    

    function set_install_btn_to_download(release_url) {
        setup_install_btn('btn-primary', 'icon-cy-install-download', 'Download',
            function() {
                window.location.href = release_url;
            });
    }

    function set_install_btn_to_installing() {
        setup_install_btn('btn-info', 'icon-cy-install-install', 'Installing...');
    }

    function set_install_btn_to_install(app_name, latest_release_version) {
        setup_install_btn('btn-info', 'icon-cy-install-install', 'Install',
            function() {
                set_install_btn_to_installing();
                install_app(app_name, latest_release_version, function(result) {
                    if (result) {
                        CyMsgs.add_msg(app_name + ' has been installed! Go to Cytoscape to use it.', 'success');
                        set_install_btn_to_installed();
                    } else {
                        CyMsgs.add_msg('Could not install &ldquo;' + app_name + '&rdquo; app: <tt>' + result['install_status'] + '</tt>', 'error');
                        set_install_btn_to_install(app_name, latest_release_version);
                    }
                });
            });
    }

    function set_install_btn_to_upgrading() {
        setup_install_btn('btn-warning', 'icon-cy-install-upgrade', 'Upgrading...');
    }

    function set_install_btn_to_upgrade(app_name, latest_release_version) {
        setup_install_btn('btn-warning', 'icon-cy-install-upgrade', 'Upgrade',
            function() {
                set_install_btn_to_upgrading();
                install_app(app_name, latest_release_version, function(result) {
                    if (result) {
                        CyMsgs.add_msg(app_name + ' has been updated! Go to Cytoscape to use it.', 'success');
                        set_install_btn_to_installed();
                    } else {
                        CyMsgs.add_msg('Could not update &ldquo;' + app_name + '&rdquo; app: <tt>' + result['install_status'] + '</tt>', 'error');
                        set_install_btn_to_install(app_name, latest_release_version);
                    }
                });
            });
    }

    function set_install_btn_to_installed() {
        setup_install_btn('btn-success', 'icon-cy-install-installed', 'Installed');
    }

    function setup_install(app_name, app_fullname, latest_release_url, latest_release_version, install_app_help_url) {
        set_install_btn_to_download(latest_release_url);

        is_manager_running(function(is_running) {
            if (is_running) {
                get_app_status(app_fullname, function(app_status) {
                    if (!app_status) {
                        set_install_btn_to_install(app_fullname, latest_release_version);
                    } else {
                        get_app_updates(app_fullname, function(app_updates) {
                            if (!app_updates) {
                                set_install_btn_to_installed();
                            } else {
                                set_install_btn_to_upgrade(app_fullname, latest_release_version);
                            }
                        })
                    }
                });
            } else {
                CyMsgs.add_msg('Want an easier way to install apps? <a href="' + install_app_help_url + '" target="_blank">Click here</a> to learn how!', 'info');
            }
        });
    }

    /*
     ================================================================
       Install a service app via the Desktop Service App
     ================================================================
       desktop-service-app adds the serviceapps commands to Cytoscape
       Desktop; CyREST serves them at /v1/commands/serviceapps/...
    */

    var ServiceRequestTimeoutMs = 10000;

    function escape_html(text) {
        return $('<div>').text(String(text)).html();
    }

    // serviceapps list replies with its JSON array on one line, followed by
    // CyREST's "Finished"; CyREST may wrap each line in <p> tags.
    function parse_service_list(reply) {
        var lines = String(reply).replace(/<[^>]*>/g, '\n').split('\n');
        for (var i = 0; i < lines.length; i++) {
            var line = $.trim(lines[i]);
            if (line.charAt(0) === '[') {
                var list = JSON.parse(line);
                if ($.isArray(list))
                    return list;
            }
        }
        throw new Error('no service app list in reply');
    }

    function version_parts(version) {
        if (!/^\d+(\.\d+)*$/.test(version))
            return null;
        var parts = $.map(version.split('.'), function(part) { return parseInt(part, 10); });
        while (parts.length > 1 && parts[parts.length - 1] === 0)
            parts.pop();
        return parts;
    }

    // -1, 0 or 1 comparing dot-separated numeric versions; null if either isn't numeric
    function compare_versions(a, b) {
        var pa = version_parts(String(a)), pb = version_parts(String(b));
        if (!pa || !pb)
            return null;
        for (var i = 0; i < Math.max(pa.length, pb.length); i++) {
            var x = i < pa.length ? pa[i] : 0, y = i < pb.length ? pb[i] : 0;
            if (x !== y)
                return x < y ? -1 : 1;
        }
        return 0;
    }

    function strip_trailing_slashes(url) {
        return String(url).replace(/\/+$/, '');
    }

    // 'install', 'installed' or 'upgrade' for the store's latest release,
    // given the service apps installed in Desktop
    function service_install_state(installed_apps, release) {
        var installed = null;
        $.each(installed_apps, function(i, app) {
            if (app.name === release.name)
                installed = app;
        });
        if (!installed)
            return 'install';
        var cmp = compare_versions(installed.version, release.version);
        if (cmp === null)
            cmp = installed.version === release.version ? 0 : -1;
        if (cmp > 0)
            return 'installed';
        if (cmp < 0)
            return 'upgrade';
        return strip_trailing_slashes(installed.url) === strip_trailing_slashes(release.url) ? 'installed' : 'upgrade';
    }

    function setup_service_install(opts) {
        var cyrest_url = opts.cyrest_url || AppManagerURL;

        function set_btn(btn_class, icon_class, btn_text, tooltip, func) {
            setup_install_btn(btn_class, icon_class, btn_text, func);
            if (tooltip)
                install_btn.attr('title', tooltip);
            else
                install_btn.removeAttr('title');
        }

        function set_btn_unavailable(tooltip) {
            set_btn('', 'icon-info-sign', 'Install in Cytoscape Desktop', tooltip);
        }

        function set_btn_to_installed() {
            set_btn('btn-success', 'icon-cy-install-installed', 'Installed in Cytoscape Desktop');
        }

        function set_btn_for_state(state) {
            if (state === 'installed') {
                set_btn_to_installed();
            } else if (state === 'upgrade') {
                set_btn('btn-warning', 'icon-cy-install-upgrade', 'Upgrade in Cytoscape Desktop', null,
                    function() { install('upgrade'); });
            } else {
                set_btn('btn-info', 'icon-cy-install-install', 'Install in Cytoscape Desktop', null,
                    function() { install('install'); });
            }
        }

        function install(state) {
            set_btn('btn-info', 'icon-refresh cy-spin', state === 'upgrade' ? 'Upgrading...' : 'Installing...');
            var url = cyrest_url + '/commands/serviceapps/install' +
                '?name=' + encodeURIComponent(opts.name) +
                '&version=' + encodeURIComponent(opts.version) +
                '&url=' + encodeURIComponent(opts.url);
            function failed(reason) {
                CyMsgs.add_msg('Could not install &ldquo;' + escape_html(opts.name) + '&rdquo; in Cytoscape Desktop: <tt>' +
                    escape_html(reason) + '</tt>', 'error', 'cy-service-install');
                set_btn_for_state(state);
            }
            $.ajax(url, {
                'type': 'GET',
                'dataType': 'text',
                'timeout': ServiceRequestTimeoutMs,
                'success': function(reply) {
                    if (String(reply).indexOf('installed') === -1) {
                        failed(reply);
                        return;
                    }
                    // count the Desktop install; best effort, it doesn't change what the user sees
                    $.ajax(opts.beacon_url, {'type': 'GET'});
                    CyMsgs.add_msg(escape_html(opts.name) + ' has been installed in Cytoscape Desktop! Go to Cytoscape to use it.',
                        'success', 'cy-service-install');
                    set_btn_to_installed();
                },
                'error': function(xhr, text_status) {
                    if (text_status === 'timeout')
                        failed('Cytoscape Desktop did not answer within ' + (ServiceRequestTimeoutMs / 1000) + ' seconds');
                    else
                        failed($.trim(xhr.responseText || '') || 'Cytoscape Desktop could not be reached');
                }
            });
        }

        function desktop_not_running() {
            set_btn_unavailable('Start Cytoscape Desktop 3.10 or later, then reload this page.');
            CyMsgs.add_msg('Start Cytoscape Desktop to install this service app. <a href="' + opts.help_url +
                '" target="_blank">Click here</a> to learn how!', 'info', 'cy-service-install');
        }

        function service_app_missing() {
            var reason = 'Desktop needs the Service App installed first to enable service app installation';
            set_btn_unavailable(reason + '.');
            CyMsgs.add_msg(reason + ': <a href="' + opts.service_app_url + '">get the Desktop Service App</a>.',
                'info', 'cy-service-install');
        }

        function list_unreadable() {
            set_btn_unavailable("Couldn't read installed service apps from Cytoscape Desktop.");
        }

        set_btn('', 'icon-refresh cy-spin', 'Checking Cytoscape Desktop...');

        $.ajax(cyrest_url, {
            'type': 'GET',
            'dataType': 'text',
            'timeout': ServiceRequestTimeoutMs,
            'error': desktop_not_running,
            'success': function() {
                $.ajax(cyrest_url + '/commands/serviceapps/list', {
                    'type': 'GET',
                    'dataType': 'text',
                    'timeout': ServiceRequestTimeoutMs,
                    'success': function(reply) {
                        var installed_apps;
                        try {
                            installed_apps = parse_service_list(reply);
                        } catch (e) {
                            list_unreadable();
                            return;
                        }
                        set_btn_for_state(service_install_state(installed_apps, opts));
                    },
                    'error': function(xhr) {
                        if (xhr.status === 404)
                            service_app_missing();
                        else if (xhr.status === 0)
                            desktop_not_running();
                        else
                            list_unreadable();
                    }
                });
            }
        });
    }

    function setup_cy_2x_download_popover(plugins_dir_img) {
        $('.cy-app-2x-download-popover').popover({
            'title': 'How to Install',
            'html': true,
            'content': '<p>Download to your <strong>plugins</strong> folder.</p><p align="center"><img style="margin-top: 1em;" src="' + plugins_dir_img + '"></p>',
            'placement': 'bottom',
            'trigger': 'hover',
        });
    }

    /*
     ================================================================
       Stars
     ================================================================
    */

    function rating_to_width_percent(rating) {
        return Math.ceil(100 * rating / 5);
    }

    function width_percent_to_rating(width_percent) {
        return Math.ceil(width_percent * 5 / 100);
    }

    function cursor_x_to_rating(cursor_x, stars_width) {
        var rating = 5 * cursor_x / stars_width;
        if (rating <= 0.5)
            return 0;
        else if (rating > 5.0)
            return 5;
        else
            return Math.ceil(rating);
    }

    function setup_rate_popover(popover) {
        var stars_tag = $('.popover-content .rating-stars');
        var stars_full_tag = $('.popover-content .rating-stars-filled');
        var rating = 5;
        $('.popover-title .close').click(function() {
            popover.popover('toggle');
        });
        $('.popover-content .rating-stars').mousemove(function(e) {
            var potential_rating = cursor_x_to_rating(e.pageX - $(this).offset().left, $(this).width());
            var width_percent = rating_to_width_percent(potential_rating);
            stars_full_tag.css('width', width_percent + '%');
        }).click(function() {
            rating = width_percent_to_rating(parseInt(stars_full_tag.css('width')));
            $('.popover-content #rate-btn #rating').text(rating);
        }).mouseleave(function() {
            var width_percent = rating_to_width_percent(rating);
            stars_full_tag.css('width', width_percent + '%');
        });
        $('.popover-content #rate-btn').click(function() {
            $(this).text('Submitting...').attr('disabled', 'true');
            $.post('', {
                'action': 'rate',
                'rating': rating
            }, function(data) {
                popover.off('click').popover('destroy').css('cursor', 'default');
                popover.find('.rating-stars-filled').css('width', data.stars_percentage.toString() + '%');
                $('#rating-count').text('(' + data.votes.toString() + ')');
                popover.tooltip({
                    'title': 'Your rating has been submitted. Thanks!'
                }).tooltip('show');
                setTimeout(function() {
                    popover.tooltip('hide');
                }, 5000);
            });
        });
    }

    function setup_stars() {
        var stars_tag = $('#app-usage-info .rating-stars');
        var stars_empty_tag = $('#app-usage-info .rating-stars-empty');
        var stars_full_tag = $('#app-usage-info .rating-stars-filled');
        stars_tag.popover({
            'trigger': 'manual',
            'content': $('#rate-popover-content').html()
        }).click(function() {
            stars_tag.popover('toggle');
            setup_rate_popover($(this));
        });
        stars_empty_tag.click(stars_tag.click);
        stars_full_tag.click(stars_tag.click);
    }


    function setup_details() {
        MarkdownUtil.format($('#cy-app-details-md'));
    }

    /*
	 ================================================================
        Release Notes
      ================================================================
     */

    function setup_release_notes() {
        $('.cy-app-release-notes').each(function() {
            MarkdownUtil.format($(this));
        });

        $('.timeago').timeago();
    }

    /*
     ================================================================
       Init
     ================================================================
    */

    return {
        'setup_url_copy': setup_url_copy,
        'setup_install': setup_install,
        'setup_service_install': setup_service_install,
        'setup_cy_2x_download_popover': setup_cy_2x_download_popover,
        'setup_stars': setup_stars,
        'setup_details': setup_details,
        'setup_release_notes': setup_release_notes,
    }
})($);
