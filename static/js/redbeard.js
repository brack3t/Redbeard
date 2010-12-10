jQuery.expr[':'].Contains = function(a, i, m) {
    return (a.textContent || a.innerText || "").toUpperCase().indexOf(m[3].toUpperCase())>=0;
}

function listFilter(header, list) {
    var form = $("<form>").attr({"class": "filterform", "action": "#"}),
        input = $("<input>").attr({"class": "filterinput", "type": "search"});

    $(form).append(input).appendTo(header);

    $(input).change(function() {
        var filter = $(this).val();
        if (filter) {
            $(list).find("a:not(:Contains(" + filter + "))").parent().slideUp();
            $(list).find("a:Contains(" + filter + ")").parent().slideDown();
        } else {
            $(list).find("li").slideDown();
        }
    }).keyup(function() {
        $(this).change();
    });
}

jQuery(window).hashchange(function() {
    var link = "/key/" + window.location.hash.replace("#", "");
    $.get(link, function(data) {
        $('#right').html(data);
    });
});

$(function() {
	listFilter($("#keyheader"), $("#keylist"));

    if (window.location.hash) {
        var link = "/key/" + window.location.hash.replace("#", "");
        $.get(link, function(data) {
            $('#right').html(data);
        });
    }

    $("a", "#keylist").live('click', function(e) {
        var link = $(this).attr('href'),
            hash = link.replace("/key/", "");
        e.preventDefault();
        $.get(link, function(data) {
            $('#right').html(data);
            window.location.hash = hash;
        });
    });

    $("#redis_db").live('change', function() {
        $(this).parent('form').submit();
    });
});
