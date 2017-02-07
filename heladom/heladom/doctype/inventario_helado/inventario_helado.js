// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inventario Helado', {
	refresh: function(frm) {
		if (!frm.doc.is_local) {
			var date = moment();
			var year = date.year();
			var week = date.isoWeek();

			frappe.model.set_value(frm.doctype,
	                    frm.docname, "week_year", year + "." + week);

			frappe.model.set_value(frm.doctype,
	                    frm.docname, "week", week);
		}

	},
	code: function(frm){
		if (frm.doc.code) {
			get_sku_info(frm, frm.doc.code);
		}
	}
});

frappe.ui.form.on('Inventario Helado items', {
	sku: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.call({
			"method": "heladom.heladom.doctype.inventario_helado.inventario_helado.get_sku_info",
			args: {
				"sku": row.sku
			},
			callback: function(data){
				var sku = data.message;
				if (sku != "error") {
					row.sku_generic = sku.generic;
					row.sku_generic_name = sku.generic_name;
					cur_frm.refresh();
				} else {
					frappe.msgprint("No se ha encontrado ningun sku con este codigo.");
				}
			}
		});
	}
});

function get_sku_info(frm, skuCode){
	frappe.call({
		"method": "heladom.heladom.doctype.inventario_helado.inventario_helado.get_sku_info",
		args: {
			"sku": skuCode
		},
		callback: function(data){
			var sku = data.message;
			if (sku != "error") {
				var row = get_sku(frm.doc.items, skuCode);

				if(! row){
					row = frappe.model.add_child(frm.doc, "items");
				}

				row.sku = sku.name;
				row.sku_name = sku.item;
				row.sku_generic = sku.generic;
				row.sku_generic_name = sku.generic_name;
				cur_frm.refresh();
				frappe.model.set_value(frm.doctype, frm.docname, "code", undefined);
				var len = document.getElementsByClassName("close btn-open-row").length;
				for(index = 0; index < len; index ++){
					btn = document.getElementsByClassName("close btn-open-row")[index];
					if((index+1) == len){
						btn.click();
					}
				}
				setTimeout(function(){ $("input[data-fieldname=sku_unces]").focus(); },500);
			} else {
				frappe.msgprint("No se ha encontrado ningun sku con este codigo.");
				after(method=frappe.hide_msgprint, instant=false, time=4);
			}
		}
	});
}

function after(method, args=undefined, time=5){ if(!method){ return; } setTimeout(function(){ method(args);},time*1000); }

function get_sku(array, sku){
	for(index = 0; index < array.length; index ++){
		if(array[index].sku == sku) return array[index];
	}

	return undefined;
}