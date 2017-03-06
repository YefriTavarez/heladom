// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Generador de Estimaciones', {
	refresh: function(frm) {
		frm.disable_save();
		frm.trigger("date");
	},
	date: function(frm){
		if(! frm.doc.date) return ;

		var date_obj = new Date(frm.doc.date);
		var moment_obj = moment(date_obj).utc();


		frm.doc.start_date = frappe.datetime.add_months(frm.doc.date, -12);
		frm.doc.end_date = frm.doc.date;
		frm.doc.year_week = moment_obj.year() + "." + moment_obj.isoWeek();
	},
	crear_estimaciones: function(frm){
		var callback = function(response){
			if(!response.message){ console.log(response); return ; }
			var header = "<h3>Estimaciones creadas</h3>";
			var link_template = "<a href=\"/desk#Form/Estimacion%20de%20Compra/name\">name</a>";
			var stimation_list = response.message;
			var body = "";

			body = body + header;

			stimation_list.forEach(function(stimation){
				var new_line = "<br>";
				var link = link_template.replace("name\">name", stimation + "\">" + stimation);

				body = body + link;
				body = body + new_line;
			});
			
			if(stimation_list.length){
				frm.set_df_property("log", "options", body);
			}
		};

		frm.set_df_property("log", "options", " ");
		$c('runserverobj', args={ 'method': 'crear_estimaciones', 'docs': frm.doc }, callback=callback);
	}
});

function $c(command, args, callback, error, no_spinner, freeze_msg, btn) {
	//console.warn("This function '$c' has been deprecated and will be removed soon.");
	return frappe.request.call({
		type: "POST",
		args: $.extend(args, {cmd: command}),
		success: callback,
		error: error,
		btn: btn,
		freeze: freeze_msg,
		show_spinner: !no_spinner
	})
}
