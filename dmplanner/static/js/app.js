const color_success = "#28a745";
const color_grey = "#e8e8e8";

$(document).ready(function () {
	$('[data-toggle="tooltip"]').tooltip();
});


/*
 * search orcid for name
 */
$(document).ready(function () {
	$("#button_search_orcid").click(function (e) {

		remove_success($("#name_check"));
		replace_with_spinner($("#orcid_people"));

		req = $.ajax({
			type: "POST",
			url: "/search_orcid/",
			data: {name: $("#input_search_orcid").val()}
		});

		req.done(function (data) {
			$("#orcid_people").html(data);

			$(".orcid_row").click(function (e) {
				display_orcid_record($(e.target.parentNode).data("orcid"));
			});
		});

	});
});


function display_orcid_record(orcid) {
	let orcid_people = $("#orcid_people");
	replace_with_spinner(orcid_people);

	req = $.ajax({
		type: "GET",
		url: "/search_orcid/",
		data: {orcid: orcid}
	});

	req.done(function (data) {
		orcid_people.html(data);
		set_to_success($("#name_check"));
		$("#input_search_orcid").val(null);
		add_work_titles(orcid);
	});
}


// get orcid work titles and add them as selectable options
function add_work_titles(orcid) {
	req = $.ajax({
		type: "GET",
		url: "/work_titles/",
		data: {orcid: orcid}
	});

	req.done(function (data) {
		$("#select_title").html(data);
		remove_success($("#title_check"));
	});
}


/*
 * add resources
 */
$(document).ready(function () {
	$("#button_add_resource").click(function (e) {

		input_value = $("#input_add_resource").val();

		if (!input_value) {
			return;
		}

		replace_with_spinner($("#resources_loading"));

		req = $.ajax({
			type: "POST",
			url: "/add_resource/",
			data: {resource_text: input_value}
		});

		req.done(function (data) {

			let resource_id = $(data).attr("id");
			let div_resources = $("#resources");

			// check if resource already exists
			if (document.getElementById(resource_id) != null) {
				display_notification('Resource already exists.', 'danger', 3000);
				return;
			}

			div_resources.append(data);
			resource_type_handler();
			$("#input_add_resource").val(null);
		});

		req.fail(function (jqXHR, textStatus, errorThrown) {
			display_notification(jqXHR.responseText, 'danger', 3000);
		});

		req.always(function () {
			$("#resources_loading").empty();
		});

	});
});


function remove_resource(resource) {
	let result = confirm("Do you really want to remove this resource?");
	if (result) {
		resource.parentNode.parentNode.remove();
		if ($("#resources div").length == 0) {
			remove_success($("#resources_check"));
		} else {
			resource_type_handler();
		}

		update_preservation_time_display()
	}
}


// handle onchange functionality of resource type selectors
function resource_type_handler() {
	let success = true;
	$(".resource_type").each(function () {
		if ($(this).val() == null) {
			success = false;
		}
	});

	let resources_check = $("#resources_check");
	if (success) {
		set_to_success(resources_check);
	} else {
		remove_success(resources_check);
	}

	update_preservation_time_display();
	preservation_time_handler();
}


// check for each preservation type if a matching resource exists and hide/show accordingly
function update_preservation_time_display() {
	time_selectors = $(".preservation_time");
	time_selectors.each(function () {
		let time_selector = $(this);
		let type = time_selector.attr("id").split("_")[1];
		let matching_resource_exists = false;

		$(".resource_type option:selected").each(function () {
			resource_type = $(this).html().split(" ")[0];

			if (type === resource_type) {
				matching_resource_exists = true;
				time_selector.parent().parent().show();
			}
		});

		if (!matching_resource_exists) {
			time_selector.parent().parent().hide();
		}
	});

	preservation_time_handler();
}


// check if all visible preservation time selectors contain a value,
// if no selectors are visible the check is set so false since resources and therefore at least one time selector is required
function preservation_time_handler() {
	let success = true;
	time_check = $("#time_check");

	let visible_selectors = $(".preservation_time:visible");

	if (visible_selectors.length === 0) {
		remove_success(time_check);
		return;
	}

	visible_selectors.each(function () {
		if ($(this).val() === null) {
			success = false;
		}
	});

	if (success) {
		set_to_success(time_check);
	} else {
		remove_success(time_check);
	}
}


function title_select_handler() {
	let title_check = $("#title_check");

	if ($("#title_select").val() === null) {
		remove_success(title_check)
	} else {
		set_to_success(title_check);
	}
}


function title_input_handler(element) {
	let select_title = $("#select_title");
	let title_check = $("#title_check");

	if ($(element).val()) {
		select_title.prop("selectedIndex", 0);
		select_title.prop('disabled', true);
		set_to_success(title_check);
	} else {
		remove_success(title_check);
		select_title.prop('disabled', false);
	}
}


function generate_dmp() {
	let dmp_human_inline = $("#dmp_human_inline");
	let dmp_machine_inline = $("#dmp_machine_inline");

	replace_with_spinner(dmp_human_inline);
	replace_with_spinner(dmp_machine_inline);

	let data = {};
	data["orcid"] = $("#data_orcid").attr("data-orcid");
	data["resources"] = [];
	data["times"] = [];

	$("#resources").children().each(function () {
		let resource = $(this);
		data['resources'].push({
			id: resource.attr("id"),
			host: resource.attr("data-host"),
			tag: resource.find(".resource_type").val()
		});
	});

	$(".preservation_time:visible").each(function () {
		let time = $(this);
		let time_object = {};
		time_object[time.attr("data-type")] = parseInt(time.val());
		data["times"].push(time_object);
	});

	input_title = $("#input_title");
	if (input_title.val()) {
		data["title"] = input_title.val();
	} else {
		data["title"] = $("#select_title").val();
	}

	req_human = $.ajax({
		type: "POST",
		url: "/generate_human_dmp/",
		data: JSON.stringify(data)
	});

	req_human.done(function (data) {
		dmp_human_inline.html(data);
		$('html, body').animate({
			scrollTop: (dmp_human_inline.offset().top)
		}, 500);
	});

	req_machine = $.ajax({
		type: "POST",
		url: "/generate_machine_dmp/",
		data: JSON.stringify(data)
	});

	req_machine.done(function (data) {
		dmp_machine_inline.empty();
		row = $("<div></div>").addClass("row my-4 justify-content-center").appendTo(dmp_machine_inline);
		card = $("<div></div>").addClass("card col-10").appendTo(row);
		card_body = $("<div></div>").addClass("card-body").appendTo(card);
		pre = $("<pre></pre>").addClass("mb-0").appendTo(card_body);

		pre[0].innerHTML = JSON.stringify(data['dmp'], undefined, 2);
		if (data['message'] != null) {
			display_notification(data['message'], 'danger', 3000)
		}
	});
}


function replace_with_spinner(element) {
	element.empty();
	var spinner_div = $("<div></div>").addClass("text-center");
	element.append(spinner_div);
	$("<i></i>").addClass("fas fa-spinner fa-spin fa-2x").appendTo(spinner_div);
}


function is_success(element) {
	return element.data("success");
}


// if all checks are successful enable the generate dmp button
function check_success() {
	button_generate_dmp = $("#button_generate_dmp");

	if ($("#name_check").data("success") && $("#resources_check").data("success") &&
		$("#time_check").data("success") && $("#title_check").data("success")) {

		button_generate_dmp.prop("disabled", false);
	} else {
		button_generate_dmp.prop("disabled", true);
	}
}


function set_to_success(element) {
	element.css("color", color_success);
	element.data("success", true);
	check_success();
}


function remove_success(element) {
	element.css("color", color_grey);
	element.data("success", false);
	check_success();
}


function display_notification(message, type, delay) {
	$.notify({
		message: message
	}, {
		type: type,
		delay: delay
	});
}