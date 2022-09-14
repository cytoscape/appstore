var AppPage = (function($) {
    /*
     ================================================================
       Install via Cytoscape 3 App Manager
     ================================================================
        */

    var AppManagerURL = 'http://127.0.0.1:1234/v1';

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
        $.ajax(AppManagerURL + '/commands/apps/status?app=' + fullname, {
                'type': 'GET',
                'success': function(result) {
                    if (result.includes('Installed')) {
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
            if (license_modal.size() !== 0) {
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
                /* license modal doesn't exist in DOM */
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
                        CyMsgs.add_msg(result['name'] + ' has been installed! Go to Cytoscape to use it.', 'success');
                        set_install_btn_to_installed();
                    } else {
                        CyMsgs.add_msg('Could not install &ldquo;' + result['name'] + '&rdquo; app: <tt>' + result['install_status'] + '</tt>', 'error');
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
                        CyMsgs.add_msg(result['name'] + ' has been updated! Go to Cytoscape to use it.', 'success');
                        set_install_btn_to_installed();
                    } else {
                        CyMsgs.add_msg('Could not update &ldquo;' + result['name'] + '&rdquo; app: <tt>' + result['install_status'] + '</tt>', 'error');
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
        'setup_install': setup_install,
        'setup_cy_2x_download_popover': setup_cy_2x_download_popover,
        'setup_stars': setup_stars,
        'setup_details': setup_details,
        'setup_release_notes': setup_release_notes,
    }
})($);
