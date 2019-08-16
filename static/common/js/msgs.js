var CyMsgs = (function() {
	var alerts_tag = $('#cy-alerts');

	// Adds a message box at the top of the page.
	// Arguments:
	//  msg: an html string with the message to put in the box
	//  type: can be "error", "warning", "success", or "info", or just empty.
	//  group: name of the message group; ensures that only one message in the group is shown.
	function add_msg(msg, type, group) {
		var msg_tag = $('<div>').
			addClass('alert').
			html('<a class="close" data-dismiss="alert" href="#">&times;</a>' + msg).
			prependTo(alerts_tag).
			hide().
			slideDown('fast');

		if (type) {
			msg_tag.addClass('alert-' + type);
		}

		if (group) {
		    alerts_tag.find('.' + group).remove();
		    msg_tag.addClass(group);
		}
	}

	return {
		'add_msg': add_msg,
	};
})();
