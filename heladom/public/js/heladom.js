// set the moment locale to Spanish
moment.locale("es")

// provide namespaces for the application

frappe.provide("hm.detalle")
frappe.provide("hm.estimacion")

frappe.provide("cur_frm.doc.sku_list_prompt")
frappe.provide("cur_frm.doc.date_picker_prompt")
frappe.provide("cur_frm.doc.estimacion_de_compras")

$(document).ready(function(event) {
	$("body").css("background-color", "rgb(18, 18, 18)")
})
