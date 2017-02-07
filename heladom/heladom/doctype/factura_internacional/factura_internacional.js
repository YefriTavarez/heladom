// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Factura Internacional', {
	refresh: function(frm) {

	},
	order: function(frm){

		frappe.call({
			"method": "heladom.heladom.doctype.factura_internacional.factura_internacional.get_order_skus",
			args: {
				order: frm.doc.order
			},
			callback: function(data){
				var skus = data.message;
				skus.forEach(function(sku){

					var row = frappe.model.add_child(frm.doc, "skus");
					row.sku = sku.sku;
					row.sku_name = sku.sku_name;
					row.qty = sku.order_sku_total;
					row.estimation_reference = sku.estimation_reference;
				});

				cur_frm.refresh();
			}
		});

	}
});
