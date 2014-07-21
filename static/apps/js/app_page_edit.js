var AppPageEdit = (function($)
{
    var SaveActions = new Object();
    var save_btn_tag = $('#save-btn');
    var max_file_size_b;
    
    /* ===============================
         Utility functions
       =============================== */
    
    // Animates the removal of a DOM object.
    // Arguments:
    //  target: the jQuery DOM object to remove
    //  speed: the length of the animation--either "slow" or "fast"
    function fade_out_and_remove(target, speed) {
        target.fadeOut(speed,
            function() {
                $(this).remove();
            });
    }
        
    // For some reason, the "change" event in text fields are not properly triggered.
    // This function is a replacement for listening to change events in a text field.
    // Arguments:
    //   target: the jQuery DOM object of the text field
    //   func: function to be called when the text field changes
    function field_change(target, func) {
        target.bind('keyup cut paste', func);
    }
    
    var supported_image_types = [
        'image/png',
        'image/jpeg',
        'image/gif',
    ];
    
    var supported_image_names = supported_image_types.map(function(s) { return s.split('/')[1]; }).join(', ');
    
    // Sets up an <input type="file"> field to accept image files.
    // This will accept only image files of an acceptable file size.
    // Arguments:
    //  file_tag: a jQuery DOM object of the <input type="file"> tag
    //  img_ready: a function to be called when the user selects an acceptable
    //    image file. This function's arguments:
    //      file: a file object from the <input> field
    //      img_url: the URL to the image file the user selected
    function setup_image_chooser(file_tag, img_ready_func) {
        /*
         For good reason, JavaScript code can't access files on a disk.
         However, if the user chooses a file through the <input> tag, we
         can read it.
        */
        file_tag.change(function(e) {
            // When the user selects a file, we can pull out a File object
            var files = e.target.files;
            for (var i = 0, file; file = files[i]; i++) {
                if (file.size > max_file_size_b ) {
                    CyMsgs.add_msg('<strong>' + file.name + '</strong> is greater than 2 Mb.',  'error');
                    continue;
                }
            
                if ($.inArray(file.type, supported_image_types) === -1) {
                    CyMsgs.add_msg('<strong>' + file.name + '</strong> is not a recognized image file. The image type must be: ' + supported_image_names, 'error');
                    continue;
                }
                
                read_file(file, img_ready_func);
            }
        });
    }
    
    // This function only gets called by setup_image_chooser() when the user selects a file.
    // We have to put this in its own function and not directly in setup_image_chooser()
    // because the "file" variable in the setup_image_chooser() loop gets destroyed, thus
    // the onload() callback references the variable incorrectly. To get around this, we put the
    // onload() callback in its own function.
    function read_file(file, img_ready_func) {
        // With FileReader, the web browser reads the contents of the file
        // and creates a fake URL for us to use.
        var reader = new FileReader();
        reader.onload = function(e) {
            var img_url = e.target.result;
            img_ready_func(file, img_url);
        };
        reader.readAsDataURL(file);
    }
    
    function set_max_file_image_size(_max_file_size_b) {
        max_file_size_b = _max_file_size_b;
    }
    
    function encourage_cy3_port(){
    	CyMsgs.add_msg('<a href="http://wiki.cytoscape.org/Cytoscape_3/AppDeveloper" target="_blank">Cytoscape 3.0 is here! Time to port your 2.x plugin to a 3.x app.</a>', 'info');
    }
    
    /* ===============================
         Basic text fields
       =============================== */
        
    function setup_text_fields() {
        function field_modified(name) {
            return function() {
                SaveActions[name] = true;
                save_btn_tag.removeClass('disabled');
            };
        }
        
        field_change($('#cy-2x-plugin-download input'), field_modified('cy-2x-plugin-download'));
        field_change($('#cy-2x-plugin-version input'), field_modified('cy-2x-plugin-version'));
        field_change($('#cy-2x-plugin-release-date input'), field_modified('cy-2x-plugin-release-date'));
        field_change($('#cy-2x-versions input'), field_modified('cy-2x-versions'));
        field_change($('#cy-app-description'), field_modified('description'));
        field_change($('#cy-app-license-text input[type=text]'), field_modified('license_text'));
        $('#cy-app-license-text input[type=checkbox]').click(field_modified('license_confirm'));
        field_change($('#cy-app-website'), field_modified('website'));
        field_change($('#cy-app-tutorial'), field_modified('tutorial'));
        field_change($('#cy-app-citation'), field_modified('citation'));
        field_change($('#cy-app-coderepo'), field_modified('coderepo'));
        field_change($('#cy-app-contact'), field_modified('contact'));
    }
        
    /* ===============================
         Icon selection
       =============================== */
        
    function setup_icon_selection(max_dim_px) {
        var app_icon_tag = $('#cy-app-icon');
        var icon_file_chooser_tag = $('#cy-app-icon-file-chooser');
        
        setup_image_chooser(icon_file_chooser_tag, function(file, img_url) {
            app_icon_tag.attr('src', img_url);
            SaveActions['icon'] = file;
            save_btn_tag.removeClass('disabled');
        });
        
        app_icon_tag.click(function() {
            icon_file_chooser_tag.click();
        }).load(function() {
            resize_icon_img($(this), max_dim_px);
        });
    }
    
    function resize_icon_img(img_tag, max_dim_px) {
        var w = img_tag[0].width;
        var h = img_tag[0].height;
        if (w > max_dim_px || h > max_dim_px) {
            if (h > w) {
                w = max_dim_px * w / h;
                h = max_dim_px;
            } else {
                h = h / (w * max_dim_px);
                w = max_dim_px;
            }
            img_tag.attr('width', w);
            img_tag.attr('height', h);
            CyMsgs.add_msg('The image will be scaled down because it has dimensions greater than ' + max_dim_px + 'x' + max_dim_px + ' px.', 'warning');
        }
    }
        
    /* ===============================
         Tags
       =============================== */
    
    var tags_list_tag = $('#cy-app-tags-list');
    
    function tags_modified() {
        SaveActions['tags'] = true;
        save_btn_tag.removeClass('disabled');
    }
        
    function add_tag(tag, animate) {
        // if we already have the tag we're adding, delete it first
        tags_list_tag.find('.cy-app-tag').each(function() {
            var current_tag_name = $(this).find('.cy-app-tag-name').text();
            if (tag === current_tag_name) {
                fade_out_and_remove($(this), 'slow');
            }
        });
        
        var tag_tag = $('#cy-tag-tmpl').tmpl({'tag': tag}).appendTo(tags_list_tag);
        setup_remove_tag_btn(tag_tag);
        
        if (animate)
            tag_tag.hide().fadeIn('fast');
    }
    
    // Each tag box has an X. When the user clicks the X, remove the box.
    function setup_remove_tag_btn(tag_tag) {
        tag_tag.find('.cy-app-tag-remove').click(function() {
            fade_out_and_remove($(this).parent(), 'fast');
            tags_modified();
        });
    }
            
    var add_tag_btn = $('#cy-app-tag-add-btn');
    
    // Toggles the add tag popover and the button state
    function toggle_add_tag() {
        add_tag_btn.toggleClass('active');
        add_tag_btn.popover('toggle');
    }
    
    // There isn't a convenient way to include JavaScript code inside
    // the popover. So we call this function to set up the popover when
    // the user opens it by clicking on the "Add Tag" button.
    function setup_add_tag_popover() {
        $('.popover-title .close').click(toggle_add_tag);
        $('#cy-tag-add-popover a').click(function() {
            add_tag($(this).text(), true);
            tags_modified();
            toggle_add_tag();
        });
        var add_btn = $('#cy-tag-add-popover button');
        var add_field = $('#cy-tag-add-popover input');
        field_change(add_field, function() {
            if ($(this).val().length)
                add_btn.removeClass('disabled');
            else
                add_btn.addClass('disabled');
        });
        add_btn.click(function() {
            if ($(this).hasClass('disabled'))
                return;
            add_tag(add_field.val(), true);
            tags_modified();
            toggle_add_tag();
        });
    }
    
    function setup_add_tag_btn() {
        add_tag_btn.popover({
            'title': 'Select a Tag to Add <a class="close">&times;</a>',
            'html': true,
            'content': $('#cy-tag-add-popover-html').html(),
            'placement': 'bottom',
            'trigger': 'manual'
        });
        
        add_tag_btn.click(function() {
            toggle_add_tag();
            setup_add_tag_popover();
        });
    }
    
    /* ===============================
         Screenshots
       =============================== */
        
    var screenshots_tag = $('#cy-app-screenshots');
    var delete_screenshot_btn = $('#cy-app-screenshot-delete-btn');
    
    function add_screenshot(thumbnail_url) {
        var screenshot_tag = $('<img>').attr('src', thumbnail_url).appendTo(screenshots_tag);
        screenshot_tag.click(function() {
            setup_select_screenshot($(this));
        });
        return screenshot_tag;
    }
    
    function setup_select_screenshot(screenshot_tag) {
        screenshot_tag.toggleClass('selected-screenshot');
        if (screenshots_tag.find('.selected-screenshot').length)
            delete_screenshot_btn.removeClass('disabled');
        else
            delete_screenshot_btn.addClass('disabled');
    }
    
    function scale_thumbnail(img_tag, max_height_px) {
        var w = img_tag[0].width;
        var h = img_tag[0].height;
        w = w * max_height_px / h;
        h = max_height_px;
        img_tag.attr('width', w).attr('height', h).ready(function() {
            offset = img_tag.offset().left + screenshots_tag.scrollLeft();
            screenshots_tag.animate({'scrollLeft': offset}, 500);
        });
    }
    
    /*
     Adding and deleting screenshots is a bit complicated.
     This is because there are two kinds of screenshots:
     those already on the app page, and those the user added.
     
     Those already on the app page have an attribute called "backend_id",
     which is the database ID of the screenshot.
     
     When the user adds a screenshot, the image file is put in
     the "SaveActions.screenshots" array. The index of the image
     file is put into the screenshot's "file_index" attribute.
     
     When the user deletes a screenshot that was already on the app page,
     the "backend_id" attribute is stored in the "SaveActions.delete_screenshots"
     array. When the user saves the app page, this array is sent to the server
     to delete the screenshots.
     
     If the user deletes a screenshot that was added, its "file_index" attribute
     is used to remove the image file from the "SaveActions.screenshots" array.
     The deleted image file isn't needlessly sent to the server.
    */
        
    function setup_screenshot_btns(max_height_px) {
        var screenshot_file_chooser = $('#cy-app-screenshot-file-chooser');
        
        setup_image_chooser(screenshot_file_chooser, function(file, img_url) {
            var screenshot_img = add_screenshot(img_url);
            screenshot_img.load(function() {
                scale_thumbnail($(this), max_height_px);
            });
            
            if (!SaveActions['screenshots'])
                SaveActions['screenshots'] = new Array();
            var save_index = SaveActions['screenshots'].length;
            screenshot_img.attr('file_index', save_index);
            SaveActions['screenshots'][save_index] = file;
            save_btn_tag.removeClass('disabled');
        });
        
        $('#cy-app-screenshot-add-btn').click(function() {
            screenshot_file_chooser.click();
        });
        
        $('#cy-app-screenshot-delete-btn').click(function() {
            $(this).addClass('disabled');
            screenshots_tag.find('.selected-screenshot').each(function() {
                var backend_id = $(this).attr('backend_id');
                var file_index = $(this).attr('file_index');
                if (backend_id !== undefined) {
                    if (!SaveActions['delete_screenshots'])
                        SaveActions['delete_screenshots'] = new Array();
                    SaveActions['delete_screenshots'].push(backend_id);
                } else if (file_index !== undefined) {
                    file_index = parseInt(file_index);
                    SaveActions['screenshots'][file_index] = undefined;
                }
                fade_out_and_remove($(this), 'fast');
                save_btn_tag.removeClass('disabled');
            });
        });
        
    }
        
    /* ===============================
         Details
       =============================== */
        
    function setup_details() {
        MarkdownUtil.setup_preview($('#cy-app-details'), $('#cy-app-details-preview'));
        field_change($('#cy-app-details'), function() {
            if (SaveActions['details']) return;
            SaveActions['details'] = true;
            save_btn_tag.removeClass('disabled');
        });
        
    }
    
    /* ===============================
         Editors
       =============================== */
    
    var add_editor_btn = $('#cy-app-editor-add');
    var delete_editor_btn = $('#cy-app-editor-delete');
    var editors_list = $('#editors-list');
    
    function editors_modified() {
        SaveActions['editors'] = true;
        save_btn_tag.removeClass('disabled');
    }
    
    function add_editor(email, username, animate) {
        editors_list.find('li').each(function() {
            if ($(this).attr('username') === username)
                fade_out_and_remove($(this), 'slow');
        });
        var display_text = email.length ? email : username;
        var tag = $('<li username=' + username + '><a>' + display_text + '</a></li>').appendTo(editors_list);
        tag.click(function() {
            editors_list.find('li').removeClass('active');
            $(this).addClass('active');
            delete_editor_btn.removeClass('disabled');
        });
        if (animate)
            tag.hide().show('slow');
    }
    
    function toggle_add_editor() {
        add_editor_btn.toggleClass('active').popover('toggle');
    }
    
    function setup_add_editor_popover() {
        $('.popover-title .close').click(toggle_add_editor);
        
        var add_field = $('#cy-editor-add-popover input');
        var add_btn = $('#cy-editor-add-popover button');
        
        field_change(add_field, function() {
            if ($(this).val().length)
                add_btn.removeClass('disabled');
            else
                add_btn.addClass('disabled');
        });
        
        add_btn.click(function() {
            if ($(this).hasClass('disabled'))
                return;
            var email = add_field.val();
            $(this).addClass('disabled');
            $.post('',
                   {'action': 'check_editor',
                   'editor_email': email},
                   function(username) {
                        $(this).removeClass('disabled');
                        if (username) {
                            add_editor(email, username, true);
                            add_field.val('');
                            toggle_add_editor();
                            editors_modified();
                        } else {
                            $('.popover-content .alert').slideDown('fast');
                        }
                   });
        });
        $('.popover-content .alert').hide();
    }
    
    function setup_add_editor_btn() {
        add_editor_btn.popover({
            'title': 'Add an Editor <a class="close">&times;</a>',
            'html': true,
            'content': $('#cy-editor-add-popover-html').html(),
            'placement': 'bottom',
            'trigger': 'manual'
        });
        add_editor_btn.click(toggle_add_editor);
        add_editor_btn.click(setup_add_editor_popover);
        
        delete_editor_btn.click(function() {
            if ($(this).hasClass('disabled'))
                return;
            fade_out_and_remove(editors_list.find('.active'), 'fast');
            $(this).addClass('disabled');
            editors_modified();
        });
    }
    
    /* ===============================
         Authors
       =============================== */
    
    var authors_table = $('#cy-app-authors');
    var author_tmpl = $('#cy-author-row-tmpl');

    var author_names = null;
    var institution_names = null;
    
    function authors_modified() {
        SaveActions['authors'] = true;
        save_btn_tag.removeClass('disabled');
    }
    
    function add_author(name, institution) {
        var author_tag = author_tmpl.tmpl({'name': name, 'institution': institution}).appendTo(authors_table);
        author_tag.find('button').click(function() {
            fade_out_and_remove(author_tag, 'fast');
            authors_modified();
        });
        field_change(author_tag.find('input'), authors_modified);
        update_typeahead_fields();
    }
    
    var author_add_btn = $('#cy-app-author-add');
    
    function setup_author_add_btn() {
        author_add_btn.click(function() {
            add_author(null, null);
        });
    }

    function setup_authors_dnd() {
        authors_table.tableDnD({
            'onDrop': authors_modified,
        });
    }

    function setup_authors_typeahead() {
        $.get("author_names", function(data) {
            author_names = remove_duplicates(data);
            update_typeahead_fields();
        });
        $.get("institution_names", function(data) {
            institution_names = remove_duplicates(data);
            update_typeahead_fields();
        });
    }

    function update_typeahead_fields() {
        if (author_names === null || institution_names === null) {
            return;
        }
        $('.cy-app-author-name').typeahead({source: author_names});
        $('.cy-app-author-institution').typeahead({source: institution_names});
    }

    function remove_duplicates(list) {
        var unique = [];
        $.each(list, function(i, el){
            if($.inArray(el, unique) === -1) unique.push(el);
        });
        return unique;
    }
    
    /* ===============================
         Release Notes
       =============================== */
    
    function setup_release_notes() {
        $('.timeago').timeago();
        
        $('.cy-release').each(function() {
            var release_div = $(this);
            var release_id = $(this).attr('release_id');
            var release_notes_field = $(this).find('.cy-release-notes');
            var release_notes_preview = $(this).find('.cy-release-notes-preview');
            var delete_btn = $(this).find('.cy-release-delete');
            
            MarkdownUtil.setup_preview(release_notes_field, release_notes_preview);
            field_change(release_notes_field, function() {
                if (!SaveActions['release_notes'])
                    SaveActions['release_notes'] = new Object();
                SaveActions['release_notes'][release_id] = true;
                save_btn_tag.removeClass('disabled');
            });
            
            if (delete_btn.hasClass('disabled')) {
                delete_btn.tooltip({
                    'html': true,
                    'title': 'Other apps depend on this release. Contact us or the app authors to delete this release.'
                });
            } else {
                delete_btn.click(function() {
                    if (!SaveActions['release_deletes'])
                        SaveActions['release_deletes'] = new Object();
                    SaveActions['release_deletes'][release_id] = true;
                    fade_out_and_remove(release_div);
                    save_btn_tag.removeClass('disabled');
                });
            }
        });
    }
    
    /* ===============================
         Saving & Canceling
       =============================== */
    
    var app_page_url;
    var loading_icon_url;
    
    function set_app_page_url(_app_page_url) {
        app_page_url = _app_page_url;
    }
    
    function set_loading_icon_url(_loading_icon_url) {
        loading_icon_url = _loading_icon_url;
    }
    
    function setup_cancel_btn() {
        $('#cancel-btn').click(function() {
            if (save_btn_tag.hasClass('disabled')) {
                window.location.href = app_page_url;
            } else {
                $('#cancel-modal').modal({'show': true});
            }
        });
    }
    
    /*
     Saving is pretty complicated. There's a couple reasons for this.
     
     We don't want to redundantly resubmit all of the app page's contents.
     We only want to submit the parts of the app page that have been modified.
     
     We deal with this by having the SaveActions object tell us what parts of
     the app page were changed.
     
     We don't want to submit all of the changes to the app
     page in a single POST. The user could be uploading several image files
     in one save, which can take a long time. The user should get messages about
     what files are being uploaded.
     
     To address this, we have the SaveActionsToAjax object. It is a list of functions
     that convert entries in the SaveActions object to an Ajax query. It includes
     messages telling the user what parts of the app page are being saved.
     
     We break up all the changes to the app page into separate posts.
     However, Ajax is asynchronous, which complicates submitting a series of posts.
     We could make it synchronous, but this would freeze the browser.
     
     To do a series of asynchronous Ajax queries, we pull out entries in the
     SaveActions object, then convert it to a series of Ajax queries. We use a
     recursive function to post the Ajax query, and when the query is finished,
     the function calls itself to post the next Ajax query.
    */
    
    var save_modal = $('#save-modal');
    var save_modal_body = save_modal.find('.modal-body');
    
    function add_action_msg(msg) {
        var msg_tag = $('<p>').html(msg).appendTo(save_modal_body);
        $('<img>').attr('src', loading_icon_url).appendTo(msg_tag);
    }
    
    function finish_last_action_msg() {
        var last_action = save_modal_body.find('p:last');
        if (!last_action.length) return;
        last_action.find('img').remove();
        $('<i>').addClass('icon-ok-sign').appendTo(last_action);
    }
    
    // Makes a function that returns an Ajax query for saving text fields
    function mk_field_save_action(msg, action, argument, field) {
        return function() {
            var data = new Object();
            data['action'] = action;
            data[argument] = field.val();
            
            return {
                'msg': msg,
                'data': data
            };
        };
    }
    
    // Makes a function that returns an Ajax query for saving files
    function mk_file_save_action(msg, action) {
        return function(file) {
            var data = new FormData();
            data.append('action', action);
            data.append('file', file);
            
            return {
                'msg': msg.replace('%s', file.name),
                'data': data,
                'type': 'file'
            };
        };
    }
    
    function filter_undefined(list) {
        return list.filter(function(elem) {
            return elem !== undefined;
        });
    }
    
    /*
     A list of functions for each entry in the SaveActions object to create an Ajax query.
     The function takes the SaveActions entry value as its argument. It returns an object like
     this:
      {
        'msg': <-- the message to show the user when submitting the Ajax post
        'data': <-- either an object or a FormData to be sent to the server
        'file': <-- true if the query's uploading a file
      }
    */
    var SaveActionsToAjax = {
        'cy-2x-plugin-download': mk_field_save_action('Saving 2.x plugin download link', 'save_cy_2x_plugin_download', 'cy_2x_plugin_download', $('#cy-2x-plugin-download input')),
        'cy-2x-plugin-version': mk_field_save_action('Saving 2.x plugin version', 'save_cy_2x_plugin_version', 'cy_2x_plugin_version', $('#cy-2x-plugin-version input')),
        'cy-2x-plugin-release-date': mk_field_save_action('Saving 2.x plugin release date', 'save_cy_2x_plugin_release_date', 'cy_2x_plugin_release_date', $('#cy-2x-plugin-release-date input')),
        'cy-2x-versions': mk_field_save_action('Saving supported Cytoscape 2.x versions', 'save_cy_2x_versions', 'cy_2x_versions', $('#cy-2x-versions input')),
        'description': mk_field_save_action('Saving description', 'save_description', 'description', $('#cy-app-description')),
        'license_text': mk_field_save_action('Saving license URL', 'save_license_text', 'license_text', $('#cy-app-license-text input[type=text]')),
        'license_confirm': function() {
            return {
                'msg': 'Saving license confirm',
                'data': {
                    'action': 'save_license_confirm',
                    'license_confirm': $('#cy-app-license-text input[type=checkbox]').prop('checked')
                }
            };
        },
        'website': mk_field_save_action('Saving website URL', 'save_website', 'website', $('#cy-app-website input')),
        'tutorial': mk_field_save_action('Saving tutorial URL', 'save_tutorial', 'tutorial', $('#cy-app-tutorial input')),
        'citation': mk_field_save_action('Saving citation URL', 'save_citation', 'citation', $('#cy-app-citation input')),
        'coderepo': mk_field_save_action('Saving code repository URL', 'save_coderepo', 'coderepo', $('#cy-app-coderepo input')),
        'contact': mk_field_save_action('Saving contact email', 'save_contact', 'contact', $('#cy-app-contact input')),
        'details': mk_field_save_action('Saving details', 'save_details', 'details', $('#cy-app-details')),
        'tags': function() {
            var tags = $('#cy-app-tags-list .cy-app-tag-name');
            var data = new Object();
            data['action'] = 'save_tags';
            data['tag_count'] = tags.length;
            tags.each(function(i) {
                data['tag_' + i] = $(this).text();
            });
            
            return {
                'msg': 'Saving tags',
                'data': data
            };
        },
        'icon': mk_file_save_action('Uploading icon <tt>%s</tt>',  'upload_icon'),
        'screenshots': function(screenshots) {
            var ajax_maker = mk_file_save_action('Uploading screenshot <tt>%s</tt>', 'upload_screenshot');
            // We remove all undefined values from SaveActions.screenshots before converting
            // them to Ajax queries. The SaveActions.screenshots array have undefined values
            // when the user deletes an added screenshot.
            return filter_undefined(screenshots).map(ajax_maker);
        },
        'delete_screenshots': function(delete_screenshots) {
            return delete_screenshots.map(function(screenshot_id) {
                return {
                    'msg': 'Deleteing screenshot ' + screenshot_id,
                    'data': {
                        'action': 'delete_screenshot',
                        'screenshot_id': screenshot_id
                    }
                };
            });
        },
        'editors': function() {
            var editors = $('#editors-list li');
            var data = new Object();
            data['action'] = 'save_editors';
            data['editors_count'] = editors.length;
            editors.each(function(i) {
                data['editor_' + i] = $(this).attr('username');
            });
            
            return {
                'msg': 'Saving editors',
                'data': data
            };
        },
        'authors': function() {
            var names = new Array();
            var institutions = new Array();
            authors_table.find('.cy-author-row').each(function(i) {
                var name = $(this).find('.cy-app-author-name').val();
                if (!name.length)
                    return;
                var institution = $(this).find('.cy-app-author-institution').val();
                names.push(name);
                institutions.push(institution);
            });
            
            var data = new Object();
            data['action'] = 'save_authors';
            data['authors_count'] = names.length;
            for (i in names) {
                data['author_' + i] = names[i];
                data['institution_' + i] = institutions[i];
            }
            
            return {
                'msg': 'Saving authors',
                'data': data
            };
        },
        'release_notes': function(release_ids) {
            var data = Object();
            data['action'] = 'save_release_notes';
            var count = 0;
            for (release_id in release_ids) {
                data['release_id_' + count] = release_id;
                data['notes_' + count] = $('[release_id=' + release_id + '] .cy-release-notes').val();
                count++;
            }
            data['release_count'] = count;
            return {
                'msg': 'Saving release notes',
                'data': data
            };
        },
        'release_deletes': function(release_ids) {
            var data = Object();
            data['action'] = 'delete_release';
            var count = 0;
            for (release_id in release_ids) {
                data['release_id_' + count] = release_id;
                count++;
            }
            data['release_count'] = count;
            return {
                'msg': 'Deleting releases',
                'data': data
            };
        },
    }
    
    
    var queue = new Array();
    
    // Pulls out an entry from SaveActions, converts it to an Ajax query, and stores it in queue.
    // If there are no more entries in SaveActions, this returns false.
    function next_action() {
        for (action in SaveActions) {
            var value = SaveActions[action];
            delete SaveActions[action];
            var query = SaveActionsToAjax[action](value);
            if (query instanceof Array)
                queue = queue.concat(query);
            else
                queue.push(query);
            return true;
        }
        return false;
    }
    
    // Goes through the queue and submits Ajax queries.
    // When the queue is empty, it gets more queries by calling next_action().
    // If next_action() says there are no more queries by returning false, this exits.
    // When the Ajax query is done, this function is called again to submit the
    // next query.
    function process_queue() {
        finish_last_action_msg();
        
        if (!queue.length) {
            if (!next_action()) {
                window.location.href = app_page_url;
                return;
            }
        }
        
        var request = queue.pop();
        if (!request) {
            process_queue();
            return;
        }
        
        add_action_msg(request.msg);
        if (request.type === 'file') {
            $.ajax({
                'url': '',
                'data': request.data,
                'cache': false,
                'contentType': false,
                'processData': false,
                'type': 'POST',
                'success': process_queue
            });
        } else {
            $.post('', request.data, process_queue);
        }
    }
    
    function validate_input() {
        var all_valid = true;
        $('[validate_regexp]').each(function() {
            var regexp_str = $(this).attr('validate_regexp');
            var regexp = new RegExp(regexp_str);
            var val = $(this).find('input[type=text]').val();
            valid = (!val.length) || regexp.test(val);
            if(valid) {
                $(this).removeClass('error');
            } else {
                $(this).addClass('error');
            }
            all_valid &= valid;
        });
        
        if (!all_valid)
            CyMsgs.add_msg('Whoops! Please fix the fields in red. Once you\'re done, click Save again.', 'error', 'save');
        return all_valid;
    }
    
    function setup_save_btn() {
        $('#save-btn').click(function() {
            if ($(this).hasClass('disabled'))
                return;
            
            if (!validate_input()) {
                $(this).addClass('disabled');
                return;
            }
            save_modal.modal({'keyboard': false, 'show': true});
            process_queue();
        });
    }
    
    return {
    	'encourage_cy3_port': encourage_cy3_port,
        'set_max_file_img_size': set_max_file_image_size,
        'setup_text_fields': setup_text_fields,
        'setup_icon_selection': setup_icon_selection,
        'add_tag': add_tag,
        'setup_add_tag_btn': setup_add_tag_btn,
        'add_screenshot': add_screenshot,
        'setup_screenshot_btns': setup_screenshot_btns,
        'setup_details': setup_details,
        'set_app_page_url': set_app_page_url,
        'set_loading_icon_url': set_loading_icon_url,
        'setup_add_editor_btn': setup_add_editor_btn,
        'add_editor': add_editor,
        'setup_author_add_btn': setup_author_add_btn,
        'add_author': add_author,
        'setup_authors_typeahead': setup_authors_typeahead,
        'setup_authors_dnd': setup_authors_dnd,
        'setup_release_notes': setup_release_notes,
        'setup_cancel_btn': setup_cancel_btn,
        'setup_save_btn': setup_save_btn,
        '_SaveActions': SaveActions,
        '_SaveActionsToAjax': SaveActionsToAjax,
    };
})($);
