// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.listview_settings["Estimacion de Compras"] = {
	add_fields: ["docstatus", "status"],
	selectable: true,
	get_indicator: function(doc) {
		if (doc.status == "Abierto") {
			return ["Abierto","orange", "docstatus,=,1|status,=,Abierto"]
		} else if (doc.status == "Ordenado") {
			return ["Ordenado","green", "docstatus,=,1|status,=,Ordenado"]
		}
	}
}