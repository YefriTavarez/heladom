// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Orden de Compra', {
	refresh: function(frm) {

	},
	on_submit: function(frm){
		validated = false;
	}
});

frappe.ui.form.on('Estimaciones Orden de Compra', {
	estimation: function(frm, cdt, cdn) {
		var current_row = locals[cdt][cdn];
		frappe.call({
			"method": "heladom.heladom.doctype.orden_de_compra.orden_de_compra.get_estimation_skus",
						args: {
								estimation: current_row.estimation
						},
						callback: function (data) {
								var skus = data.message;
								skus.forEach(function(sku){
									var row = frappe.model.add_child(frm.doc, "estimations_skus");
									row.sku = sku.sku;
									row.sku_name = sku.sku_name;
									row.general_coverage = sku.general_coverage;
									row.reqd_option_1 = sku.reqd_option_1;
									row.reqd_option_2 = sku.reqd_option_2;
									row.reqd_option_3 = sku.reqd_option_3;
									row.required_qty = sku.required_qty;
									row.order_sku_existency = sku.order_sku_existency;
									row.order_sku_in_transit = sku.order_sku_in_transit;
									row.order_sku_real_reqd = sku.order_sku_real_reqd;
									row.logistica = sku.logistica;
									row.mercadeo = sku.mercadeo;
									row.planta = sku.planta;
									row.order_sku_total = sku.order_sku_total;
									row.estimation_reference = current_row.estimation;
								});

							cur_frm.refresh();
						}
		});
	}
});

frappe.ui.form.on('Orden de Compra Productos', {
	logistica: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		row.order_sku_total = parseFloat(parseFloat(row.order_sku_total) + parseFloat(row.logistica)).toFixed(0);
		frm.refresh_field("estimations_skus");
		
	},
	mercadeo: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		row.order_sku_total = parseFloat( parseFloat(row.order_sku_total) + parseFloat(row.mercadeo)).toFixed(0);
		frm.refresh_field("estimations_skus");
		
	},
	planta: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		row.order_sku_total = parseFloat(parseFloat(row.order_sku_total) + parseFloat(row.planta)).toFixed(0);
		frm.refresh_field("estimations_skus");
	},
});