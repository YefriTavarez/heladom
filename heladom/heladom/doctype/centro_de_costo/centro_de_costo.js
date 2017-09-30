// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Centro de costo', {
	refresh: function(frm) {
		frm.trigger("set_queries")
	},
	set_queries: function(frm) {
		var events = ["set_center_admin_query"]

		$.each(events, function(idx, event) {
			frm.trigger(event)
		})
	},
	set_center_admin_query: function(frm) {
		frm.set_query("center_admin", function() {
			return {
				"query": "heladom.queries.cost_center_admins"
			}
		})
	}
})
