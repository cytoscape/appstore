var MarkdownUtil = (function() {
    var popoverContent = '                                                                                      \
        <table class="table table-striped table-condensed table-bordered">                                      \
            <thead>                                                                                             \
                <th>Result</th>                                                                                 \
                <th>Markdown</th>                                                                               \
            </thead>                                                                                            \
            <tbody>                                                                                             \
                <tr>                                                                                            \
                    <td><em>Emphasis</em></td>                                                                  \
                    <td><tt>*Emphasis*</tt></td>                                                                \
                </tr>                                                                                           \
                <tr>                                                                                            \
                    <td><strong>Strong</strong></td>                                                            \
                    <td><tt>**Strong**</tt></td>                                                                \
                </tr>                                                                                           \
                <tr>                                                                                            \
                    <td><h3>Header</h3></td>                                                                    \
                    <td><tt>### Header</tt></td>                                                                \
                </tr>                                                                                           \
                <tr>                                                                                            \
                    <td><a>http://link</a></td>                                                                 \
                    <td><tt>[http://link]</tt></td>                                                             \
                </tr>                                                                                           \
                <tr>                                                                                            \
                    <td><a>Link</a></td>                                                                        \
                    <td><tt>[http://link Link]</tt></td>                                                        \
                </tr>                                                                                           \
            </tbody>                                                                                            \
        </table>                                                                                                \
        <p><a href="/help/md" target="_blank">Click here</a> for more.</p>                                      \
    ';
    
    var converter = Markdown.getSanitizingConverter();
    
    // Returns a wrapper function so that a given function can be called
    // at most once within the given time delay.
    // Arguments:
    //  target: the function to be called, must have no arguments
    //  delay: the amount of time in milliseconds
    function throttle(target, delay) {
        return function() {
            var is_waiting = false;
            return function() {
                if (is_waiting) return;
                is_waiting = true;
                setTimeout(function() {
                    target();
                    is_waiting = false;
                }, delay);
            };
        }();
    }
    
    function setup_preview(textfield, preview) {
        function update_preview() {
            var fmt_md = textfield.val();
            var fmt_html = converter.makeHtml(fmt_md);
            preview.html(fmt_html);
        }
        
        textfield.popover({
            'trigger':   'focus',
            'title':     'Formatting with Markdown',
            'content':    popoverContent,
            'placement': 'right',
            'html':       true
        });
        
        textfield.bind('keyup cut paste', throttle(update_preview, 1000));
        
        update_preview();
    }
    
    function format(tag) {
        var fmt_md = tag.text();
        var fmt_html = converter.makeHtml(fmt_md);
        tag.html(fmt_html);
    }
    
    return {
        'setup_preview': setup_preview,
        'format': format,
    };
})();
