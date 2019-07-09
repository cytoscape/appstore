$(function() {
    function display_unsupported_msg() {
	    CyMsgs.add_msg('Your browser is not supported. Consider switching to <a href="http://www.getfirefox.com">Firefox</a>.', 'error');
    }
    
    if (!$.support.ajax) {
        display_unsupported_msg();
    }
});
