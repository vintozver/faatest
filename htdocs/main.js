var ground_school = new Object();
ground_school.notification = function(body) {
	var element = $("#ground_school_notification");
	element.children("div").html(body);
	element.show();
	setTimeout(function() {
		element.hide();
	}, 3000);
};
ground_school.notification_message = function(message) {
	ground_school.notification("<div class=\"message\">" + message + "</div>");
};
ground_school.init = function() {
	$.post(
		"/actions.py?action=load_container", {},
		function (data) {
			ground_school.update_container(data.container);
			if (data.message != null) {
				ground_school.notification_message(data.message);
			}
		},
		"json"
	);
};
ground_school.update_container = function(data) {
	if (data != null) {
		$("#ground_school_container").html(data.html);
	}
};
ground_school.on_choice_reset = function() {
	$.post(
		"/actions.py?action=choice_reset", {},
		function (data) {
			ground_school.update_container(data.container);
			if (data.message != null) {
				ground_school.notification_message(data.message);
			}
		},
		"json"
	);
};
ground_school.on_choose_group = function(GroupID) {
	if (typeof(GroupID) == "undefined") {
		GroupID = $("input:radio:checked[name=\"ground_school_input_GroupID\"]").val();
	}
	if (GroupID == null) {
		alert("Please choose group");
		return;
	}
	$.post(
		"/actions.py?action=choose_group", {"GroupID": GroupID},
		function (data) {
			ground_school.update_container(data.container);
			if (data.message != null) {
				ground_school.notification_message(data.message);
			}
		},
		"json"
	);
};
ground_school.on_choose_test = function(TestID) {
	if (typeof(TestID) == "undefined") {
		TestID = $("input:radio:checked[name=\"ground_school_input_TestID\"]").val();
	}
	if (TestID == null) {
		alert("Please choose test");
		return;
	}
	$.post(
		"/actions.py?action=choose_test", {"TestID": TestID},
		function (data) {
			ground_school.update_container(data.container);
			if (data.message != null) {
				ground_school.notification_message(data.message);
			}
		},
		"json"
	);
};
ground_school.on_practice_run = function() {
	var count = parseInt($("input:text[name=\"ground_school_ready_count\"]").val()); if (isNaN(count)) count = 0;
	var mixquestions = 0; if ($("input:checkbox:checked[name=\"ground_school_ready_mixquestions\"]").val() != null) mixquestions = 1;
	var mixanswers = 0; if ($("input:checkbox:checked[name=\"ground_school_ready_mixanswers\"]").val() != null) mixanswers = 1;
	var reportsingle = 0; if ($("input:checkbox:checked[name=\"ground_school_ready_reportsingle\"]").val() != null) reportsingle = 1;
	$.post(
		"/actions.py?action=practice_run",
		{"count": count, "mix_questions": mixquestions, "mix_answers": mixanswers, "report_single": reportsingle},
		function (data) {
			if (data.message != null) {
				ground_school.notification_message(data.message);
			}
			ground_school.update_container(data.container);
		},
		"json"
	);
};
ground_school.on_real_run = function() {
	$.post(
		"/actions.py?action=real_run", {},
		function (data) {
			if (data.message != null) {
				ground_school.notification_message(data.message);
			}
			ground_school.update_container(data.container);
		},
		"json"
	);
};
ground_school.on_survey_choose_question = function(QuestionID) {
	$.post(
		"/actions.py?action=survey_choose_question", {"QuestionID": QuestionID},
		function (data) {
			$("#ground_school_container").html(data.container.html);
		},
		"json"
	);
};
ground_school.on_survey_prev_question = function() {
	$.post(
		"/actions.py?action=survey_prev_question", {},
		function (data) {
			$("#ground_school_container").html(data.container.html);
		},
		"json"
	);
};
ground_school.on_survey_next_question = function() {
	$.post(
		"/actions.py?action=survey_next_question", {},
		function (data) {
			$("#ground_school_container").html(data.container.html);
		},
		"json"
	);
};
ground_school.on_survey_show_questions = function() {
	$.post(
		"/actions.py?action=survey_show_questions", {},
		function (data) {
			$("#ground_school_container").html(data.container.html);
		},
		"json"
	);
};
ground_school.on_survey_answer_question = function(AnswerID) {
	if (typeof(AnswerID) == "undefined") {
		AnswerID = $("input:radio:checked[name=\"ground_school_input_AnswerID\"]").val();
	}
	if (AnswerID == null) {
		alert("Please choose answer");
		return;
	}
	$.post(
		"/actions.py?action=survey_answer_question", {"AnswerID": AnswerID},
		function (data) {
			ground_school.notification(data.message);
			$("#ground_school_container").html(data.container.html);
		},
		"json"
	);
};
ground_school.on_survey_help_question_show = function() {
	$("#ground_school_survey_question").children("div.help").children("div.contents").show();
	$("#ground_school_survey_question").children("div.help").children("span.show").hide();
	$("#ground_school_survey_question").children("div.help").children("span.hide").show();
};
ground_school.on_survey_help_question_hide = function() {
	$("#ground_school_survey_question").children("div.help").children("span.hide").hide();
	$("#ground_school_survey_question").children("div.help").children("span.show").show();
	$("#ground_school_survey_question").children("div.help").children("div.contents").hide();
};
ground_school.on_survey_finish = function() {
	$.post(
		"/actions.py?action=survey_finish", {},
		function (data) {
			$("#ground_school_container").html(data.container.html);
		},
		"json"
	);
};
ground_school.on_survey_close = function() {
	$.post(
		"/actions.py?action=survey_close", {},
		function (data) {
			$("#ground_school_container").html(data.container.html);
		},
		"json"
	);
};
