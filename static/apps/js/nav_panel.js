$(function() {
    var form = $('#search');
    form.find('button').click(function() {
	form.submit();
    });
});

$(function() {
    var TAG_LIST_COOKIE = 'cytoscape.AppStore.Nav.TagList';

    function show_not_top_tags(animate) {
	$('#more-button').html('less &laquo;');
	if (animate)
	  $('#not-top-tags').slideDown('fast')
	else
	  $('#not-top-tags').show()
	$.cookie(TAG_LIST_COOKIE, 'show_all', {path: '/'});
    }

    function hide_not_top_tags(animate) {
	$('#more-button').html('more &raquo;');
	if (animate)
	  $('#not-top-tags').slideUp('fast')
	else
	  $('#not-top-tags').hide()
	$.cookie(TAG_LIST_COOKIE, 'show_some', {path: '/'});
    }

    if ($.cookie(TAG_LIST_COOKIE) === 'show_all')
	show_not_top_tags(false);
    else
	hide_not_top_tags(false);

    $('#more-button').click(function() {
	if ($('#not-top-tags').is(':visible')) {
	    hide_not_top_tags(true);
	} else {
	    show_not_top_tags(true);
	}
    });

});

$(function() {
    var TAGS_COOKIE = 'cytoscape.AppStore.Nav.Tags';

    function show_tag_list(animate) {
	$('#cy-tag-cloud').hide();
	$('#cy-tag-list').show(animate ? 'fast' : '');
	$('#cy-tag-buttons button').removeClass('active');
	$('#cy-tag-buttons #cy-tag-list-btn').addClass('active');
	$.cookie(TAGS_COOKIE, 'tag_list', {path: '/'})
    }

    function show_tag_cloud(animate) {
	$('#cy-tag-list').hide();
	$('#cy-tag-cloud').show(animate ? 'fast' : '');
	$('#cy-tag-buttons button').removeClass('active');
	$('#cy-tag-buttons #cy-tag-cloud-btn').addClass('active');
	$.cookie(TAGS_COOKIE, 'tag_cloud', {path: '/'})
    }

    if ($.cookie(TAGS_COOKIE) === 'tag_cloud')
	show_tag_cloud(false);
    else
	show_tag_list(false);
    
    $('#cy-tag-buttons #cy-tag-list-btn').click(function() {
	if (!($('#cy-tag-list').is(':visible')))
	    show_tag_list(true);
    });

    $('#cy-tag-buttons #cy-tag-cloud-btn').click(function() {
	if (!($('#cy-tag-cloud').is(':visible')))
	    show_tag_cloud(true);
    });
});