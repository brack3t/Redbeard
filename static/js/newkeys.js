var $member = $("#member").parent('fieldset');

$(".add_member").live('click', function() {
	var $new_member = $member.clone(),
        $members = $("#members"),
		count = $("[id^=member]").length,
		new_id = $new_member.find('input').attr('id') + '_' + count,
		$insert_point = $("#key_ttl").parent('fieldset');
	$("input", $new_member).attr({'id': new_id, 'name': new_id, 'value': ''});
	$("label", $new_member).attr('for', new_id);
	$new_member.appendTo($("#members"));
	$new_member.find('input').focus();
});
