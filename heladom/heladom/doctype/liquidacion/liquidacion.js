// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Liquidacion', {
	refresh: function(frm) {

	},
	international_order: function(frm){
		frappe.call({
			"method": "heladom.heladom.doctype.liquidacion.liquidacion.get_international_order_info",
			args: {
				"international_order": frm.doc.international_order
			},
			callback: function(data){
				var skus = data.message;
				skus.forEach(function(sku){
					var row = frappe.model.add_child(frm.doc, "skus");
					row.sku = sku.sku;
					row.sku_name = sku.sku_name;
					row.qty = sku.order_sku_total;
					row.arancel = sku.arancel;

					row.monto_arancel = row.qty * parseFloat(row.qty * row.arancel / 100).toFixed(2);
				});

				cur_frm.refresh();
			}
		});
	}
});
frappe.ui.form.on('Liquidacion Items', {
	arancel: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		row.monto_arancel = row.qty * parseFloat(row.qty * row.arancel / 100).toFixed(2);
		frm.refresh_field("skus");
	},
	total_cif_usd: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		row.total_cif_dop = parseFloat(row.total_cif_usd * frm.doc.rate).toFixed(2);
		frm.refresh_field("skus");
	}

});