function listFilter(header, list) {
    var form = $('<form>').attr({'class': 'filterform', 'action': '#'}),
        input = $('<input>').attr({
            'class': 'filterinput',
            'type': 'search',
            'placeholder': 'Filter'
        }),
        controls = $('<div>').attr({
            'id': 'key_controls'
        }),
        add_key = $('<a>').attr({
            'href': '/key/new/string',
            'id': 'add_key',
            'title': 'add new key'
        }).text('add new key');
        refresh = $('<a>').attr({
            'href': '/keys',
            'id': 'refresh_keys',
            'title': 'refresh available keys'
        }).text('refresh keys');


    $(controls).append(add_key).append(refresh);
    $(form).append(input).append(controls).appendTo(header);

    $(input).ajaxStart(function() {
        $(list).css({background: 'url("/static/img/ajax-loader.gif") center center no-repeat'});
    })
    .ajaxStop(function() {
        $(list).css({background: 'none'});
    })
    .ajaxSuccess(function() {
        $(list).css({background: 'none'});
    });

    $(input).change(function() {
        var filter = $(this).val();
        if (filter) {
            $(list).empty();
            var jqxhr = $.getJSON('/search/' + filter)
                .success(function(data) {
                    var items = [];
                    $.each(data['keys'], function(key, value) {
                        items.push('<li><a href="/key/' + value + '/">' + value + '</a></li>');
                    });
                    $(list).html(items.join(''));
                })
                .error(function() {
                    $(list).html('<li>An error occurred. Make sure redis is running and reload the page.</li>');
                });
        } else {
            $(list).empty();
            var jqxhr = $.getJSON('/search/' + filter)
                .success(function(data) {
                    var items = [];
                    $.each(data['keys'], function(key, value) {
                        items.push('<li><a href="/key/' + value + '/">' + value + '</a></li>');
                    });
                    $(list).html(items.join(''));
                })
                .error(function() {
                    $(list).html('<li>An error occurred. Make sure redis is running and reload the page.</li>');
                });
        }
    }).keyup(function() {
        $(this).change();
    }).blur(function() {
        $(this).change();
    });
}

$(window).hashchange(function() {
    var hash = window.location.hash.replace('#', '');
    if (hash != '') {
        var link = '/key/' + hash;
        $.get(link, function(data) {
            $('#right').html(data);
        });
        $('li', '#keylist').removeClass('current');
        $('a[href=' + link + ']', '#keylist').parent('li').addClass('current');
        $('#keylist').scrollTo('.current');
    } else {
        $('#right').empty();
    }
});

$(function() {
    listFilter($('#keyheader'), $('#keylist'));
    $(".filterform").live('submit', function(e) { e.preventDefault(); });

    if (window.location.hash) {
        var link = '/key/' + window.location.hash.replace('#', '');
        $('a[href=' + link + ']', '#keylist').parent('li').addClass('current');

        $.get(link, function(data) {
            $('#right').html(data);
        });
        $('#keylist').scrollTo('.current');
    }

    $('a', '#keylist').live('click', function(e) {
        var link = $(this).attr('href'),
            hash = link.replace('/key/', '');
        e.preventDefault();
        $('li', '#keylist').removeClass('current');
        $(this).parent('li').addClass('current');
        $.get(link, function(data) {
            $('#right').html(data);
            window.location.hash = hash;
        });
    });

    $('#id_redis_db').live('change', function() {
        $(this).parent().parent('form').submit();
    });

    $('#refresh_keys').live('click', function(e) {
        var link = $(this).attr('href');
        e.preventDefault();
        $.get(link, function(data) {
            $('#keylist').empty();
            keys = []
            for (i in data['keys']) {
                keys.push('<li><a href="/key/' + data['keys'][i] + '">' + data['keys'][i] + '</a></li>');
            }
            $('#keylist').append(keys.join(''));
            window.location.hash = '';
        });
    });
    $("#add_key").live('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        var link = $(this).attr("href");
        $.confirm({
            'title': 'Add new key',
            'message': 'Choose the new key type',
            'buttons': {
                'String': {
                    'action': function() {
                        window.location = '/key/new/string';
                    }
                },
                'List': {
                    'action': function() {
                        window.location = '/key/new/list';
                    }
                },
                'Hash': {
                    'action': function() {
                        window.location = '/key/new/hash';
                    }
                },
                'Set': {
                    'action': function() {
                        window.location = '/key/new/set';
                    }
                },
                'Sorted Set': {
                    'action': function() {
                        window.location = '/key/new/zset';
                    }
                }
            }
        });
    });
});
