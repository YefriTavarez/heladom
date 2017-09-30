// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt
var mr_items, mr_list;
frappe.ui.form.on('Movimiento de Inventario', {
	onload_post_render: function (frm) {
			if (frm.is_new()) {
				frm.set_value("item_table", []);
			}
	},
	validate: function(frm){
		if(frm.doc.pedido){
			$.each(frm.doc.item_table, function(index, value){
				var i = mr_list.indexOf(value.item_code);
				if(mr_items[i].qty !== value.cantidad){
					frappe.msgprint("Cantidad Incorrecta en Item " + value.item_code,"Error");
					validated = 0;
				}
			});
		}
	},

	pedido: function(frm){
		if(frm.doc.pedido){
			frappe.call({
				method: "frappe.client.get",
				args: {
					"doctype": "Material Request",
					"name": frm.doc.pedido
				},
				callback: function(r){
					if(
						!(r.message.workflow_state === "En Almacen" ||
						r.message.workflow_state === "En Transito")
					){
						frappe.msgprint("Pedido no Valido", "Error");
						frm.set_value("pedido", null);
					}
					var array = [], list = [];
					for(var i = 0; i < r.message.items.length; i++){
						array.push({
							item_code: r.message.items[i].item_code,
							qty: r.message.items[i].qty
						});
						list.push(r.message.items[i].item_code);
					}
					mr_items = array;
					mr_list = list;
				}
			});
		}
	},
	barcode: function(frm) {
		if(frm.doc.barcode){
			if(frm.doc.barcode.indexOf(" ") > -1){
				var index = frm.doc.barcode.indexOf(" ") - 1;
				frm.doc.barcode = frm.doc.barcode.substr(2,index);
			}
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					"doctype": "Item",
					"filters": { "barcode": frm.doc.barcode},
					"fieldname": [
						"item_code",
						"item_name",
						"stock_uom"
					]
				},
				callback: function(r){
					if(r.message){
						frm.doc.item_code = r.message.item_code;
						frm.doc.item_name = r.message.item_name;
						frm.doc.uom = r.message.stock_uom;
						frm.doc.cantidad = 1;
						frm.set_value("barcode", null);
						frm.trigger("agregar_item");
					}else{
						frappe.msgprint("Codigo de Barra Invalido", "Error");
						frm.set_value("barcode", null);
					}
				}
			});
		}
	},
	agregar_item: function(frm){
		if(mr_list.indexOf(frm.doc.item_code) === -1){
			frm.set_value("barcode", null);
			frappe.msgprint("Item no Existe en Pedido", "Error");
		}else{
			var itemList = [];
			$.each(frm.doc.item_table, function(index, value){
				itemList.push(value.item_code);
			});
			var i = itemList.indexOf(frm.doc.item_code);
			if(i !== -1){
				frm.doc.item_table[i].cantidad++;
			}else{
				frm.add_child("item_table", {
				 item_code: frm.doc.item_code,
				 item_name: frm.doc.item_name,
				 uom: frm.doc.uom,
				 cantidad: frm.doc.cantidad
				});
			}
			frm.set_value("last_item_code", frm.doc.item_code);
			frm.set_value("last_item_name", frm.doc.item_name);
			frm.set_value("last_uom", frm.doc.uom);
			frm.set_value("last_cantidad", frm.doc.cantidad);
			frm.set_value("barcode", null);
			frm.refresh_field("item_table");
		}
	}
});
