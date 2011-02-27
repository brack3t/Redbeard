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
            update_keys();
        }
    }).keyup(function() {
        $(this).change();
    }).blur(function() {
        $(this).change();
    });
}

function update_keys() {
    list = $("#keylist");
    $(list).empty();
    var jqxhr = $.getJSON('/search/')
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
    $(window).hashchange();
}

$(window).hashchange(function() {
    var hash = location.hash.replace('#', '');
    if (hash != '') {
        var link = '/key/' + hash;
        $.get(link, function(data) {
            $('#right').html(data);
        });
        $('li', '#keylist').removeClass('current');
        $('a[href="' + link + '"]', '#keylist').parent('li').addClass('current');
        $('#keylist').scrollTo('.current');
    } else {
        $('#right').empty();
    }
});

$(function() {
    listFilter($('#keyheader'), $('#keylist'));
    $(".filterform").live('submit', function(e) { e.preventDefault(); });

    if (location.hash) {
        var link = '/key/' + location.hash.replace('#', '');
        $('a[href="' + link + '"]', '#keylist').parent('li').addClass('current');

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

    $(window).hashchange();

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
    var flashes = $("#flashes");

    $("#refresh").live('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        var link = $(this).attr('href'),
            hash = link.replace("/key/", "");
        $.get(link, function(data) {
            $('#right').html(data);
            window.location.hash = hash;
        });
    });

    $("#delete").live('click', function(e) {
        e.stopPropagation();
        e.preventDefault();
        var link = $(this).attr("href");
        $.confirm({
            'title': 'Delete Confirmation',
            'message': 'Are you sure you want to delete this key?',
            'buttons': {
                'Yes': {
                    'class': 'go',
                    'action': function() {
                        $.ajax({
                            url: link,
                            dataType: "json",
                            success: function(data) {
                                flashes.empty();
                                $("<li>").text(data['flash']).appendTo(flashes);
                                $("#refresh_keys").trigger('click');
                            }
                        });
                    }
                },
                'No': {
                    'class': 'stop'
                }
            }
        });
    });

    $("#key").live('submit', function(e) {
        e.stopPropagation();
        e.preventDefault();

        var link = $(this).attr("action"),
            flashes = $("#flashes"),
            saved_name = $(this).find("input[name=saved_key_name]").val();

        flashes.empty();

        $.ajax({
            url: link,
            type: "POST",
            data: {
                "key_name": $(this).find("input[name=key_name]").val(),
                "saved_key_name": saved_name,
                "value": $(this).find("textarea").val()
            },
            dataType: "json",
            success: function(data) {
                $(this).find("textarea").val(data['value']);
                $(this).find("input[name=key_name], input[name=saved_key_name]").val(data['key']);
                $("<li>").text(data['flash']).appendTo(flashes);
                if (data['key_changed'] = 'true') {
                    location.hash = data['key'];
                    update_keys();
                }
            }
        });
    });
});
