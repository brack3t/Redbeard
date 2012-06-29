(function($) {
    $.confirm = function(params) {
        if($('#confirmOverlay').length) {
            return false;
        }

        var buttonHTML = '';
        $.each(params.buttons, function(name, obj) {
            buttonHTML += '<a href="#" class="button ' + obj['class'] + '">' + name + '</a>';

            if(!obj.action) {
                obj.action = function(){};
            }
        });

        var markup = [
            '<div id="confirmOverlay">',
            '<div id="confirmBox">',
            '<header>',
            '<h1>', params.title, '</h1>',
            '<a href="#" class="close">x</a>',
            '</header>',
            '<p>', params.message, '</p>',
            '<div id="confirmButtons">',
            buttonHTML,
            '</div></div></div>'
        ].join('');

        $(markup).hide().appendTo('body').fadeIn();

        var buttons = $('#confirmBox .button'),
            i = 0;

        $.each(params.buttons, function(name, obj) {
            buttons.eq(i++).click(function() {
                obj.action();
                $.confirm.hide();
                return false;
            });
        });

        $('#confirmOverlay').click(function() {
            $.confirm.hide();
        });

        $('#confirmBox header .close').click(function() {
            $.confirm.hide();
            return false;
        });

        $('html').bind('keydown', function(e) {
            var code = (e.keyCode ? e.keyCode : e.which);

            if (code == 27) {
                $.confirm.hide();
            }
        });
    }

    $.confirm.hide = function() {
        $('#confirmOverlay').fadeOut(function() {
            $(this).remove();
        });
    }

})(jQuery);
