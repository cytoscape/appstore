var AppPage = (function($) {
	/*
     ================================================================
       Install via Cytoscape 3 App Manager
     ================================================================
	*/

	var AppManagerURL = 'http://localhost:2607/';

	function is_manager_running(callback) {
		$.ajax(AppManagerURL + 'status/',
			{'type': 'GET',
			 'success': function() { callback(true); },
			 'error': function() { callback(false); }});
	}
	
	function get_app_status(fullname, callback) {
		$.getJSON(AppManagerURL + 'status/' + fullname,
			{},
			callback);
	}

    function install_app(app_name, app_version, callback) {
        $.getJSON(AppManagerURL + 'install/' + app_name + '/' + app_version,
            {},
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
		if (func)
			install_btn.click(func);
		else
			install_btn.addClass('disabled');
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
                    if (result['install_status'] === 'success') {
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
                    if (result['install_status'] === 'success') {
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
					if (app_status.status === 'not-found' || app_status.status === 'uninstalled') {
						set_install_btn_to_install(app_fullname, latest_release_version);
					} else if (app_status.status === 'installed') {
						var installed_version = app_status.version;

						if (installed_version === latest_release_version) {
							set_install_btn_to_installed();
						} else {
							set_install_btn_to_upgrade(app_fullname, latest_release_version);
						}
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
    
    
    function setup_stars(config) {
        var stars_tag       = $('#rating-stars');
        var stars_empty_tag = $('#rating-stars-empty');
        var stars_full_tag  = $('#rating-stars-filled');
        var extra_tag       = $('#rating-count');
        var loading_tag     = $('#rating-loading');

        function setup_avg_rating(avg_rating_percentage, votes_num) {
            stars_full_tag.css('width', avg_rating_percentage + '%');
            extra_tag.html('(' + votes_num + ')');
        }
        
        function set_to_loading() {
            extra_tag.hide();
            loading_tag.show();
        }
        
        function set_to_loading_done() {
            extra_tag.show();
            loading_tag.hide();
        }

        function remove_post_rating() {
            stars_tag.off('mouseenter').off('mousemove').off('mouseleave').off('click').css('cursor', '');
        }
        
        function setup_post_rating() {
            var original_stars;
            
            function x_to_rating(x, width) {
                var rating = 5 * x / width;
                if (rating <= 0.5)
                    return 0;
                else if (rating > 5.0)
                    return 5;
                else
                    return Math.ceil(rating);
            }
            
            function rating_to_stars(rating) {
                return 100 * rating / 5;
            }
            
            stars_tag.css('cursor', 'pointer').mouseenter(function() {
                original_stars = stars_full_tag.css('width');
            }).mousemove(function(e) {
                var rating = x_to_rating(e.pageX - $(this).offset().left, $(this).width());
                var stars = rating_to_stars(rating);
                stars_full_tag.css('width', stars + '%');
            }).mouseleave(function() {
                stars_full_tag.css('width', original_stars);
            }).click(function(e) {
                var rating = x_to_rating(e.pageX - $(this).offset().left, $(this).width());
                
                set_to_loading();
                remove_post_rating();
                $.post('', {'action': 'rate', 'rating': rating},
                    function(data) {
                        set_to_loading_done();
                        original_stars = data.stars_percentage + '%';
                        setup_avg_rating(data.stars_percentage, data.votes);
                        stars_tag.tooltip({'title': 'Your rating has been submitted. Thanks!'});
                        stars_tag.tooltip('show');
                    });
            });
        }
    
        setup_avg_rating(config.avg_rating_percentage, config.votes_num);
        
        setup_post_rating();
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
