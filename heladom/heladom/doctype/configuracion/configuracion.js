// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configuracion', {
	refresh: function(frm) {
		setTimeout(function() {
			document.activeElement 
				&& document.activeElement.blur()
		}, 100)
	},
	onload_post_render: function(frm) {
		var method = "heladom.white_listed.get_week_day_set"
		var callback = function(response) {
			var week_day_set = response.message

			if ( !week_day_set) {
				frappe.throw("Hubo un error mientras se cargaban los dias la semana.\
					¡Contacte a su administrador!")
			}

			set_field_options("default_week_day", week_day_set)
			set_field_options("default_week_day_", week_day_set)
		}

		frappe.call({ "method": method, "callback": callback })
	}
});
