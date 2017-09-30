// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

var current_uoms, uoms_list, conversion_list;

var set_cantidad = function(frm, frappe){
	console.log(uoms_list.indexOf(frm.doc.uom));
	console.log(current_uoms);
	console.log(current_uoms[uoms_list.indexOf(frm.doc.uom)].directo);
	if(current_uoms[uoms_list.indexOf(frm.doc.uom)].directo === 1){
		frm.doc.cantidad = 1;
		frm.trigger("agregar");
	}else{
		frappe.prompt(
			[
				{
					'fieldname': 'cantidad',
					'fieldtype': 'Float',
					'label': 'Cantidad',
					'reqd': 1
				}
			],
			function(values){
				frm.doc.cantidad = values.cantidad;
				frm.trigger("agregar");
			},
			'Cantidad',
			'Ok'
		);
	}
}

var set_unidad = function(frm, frappe, uoms){
	current_uoms = uoms;
	uoms_list = [];
	conversion_list = [];
	$.each(uoms, function(index, value){
		uoms_list.push(value.uom);
		conversion_list.push(value.conversion_factor);
	});
	frappe.prompt(
		[
			{
				'fieldname': 'uom',
				'fieldtype': 'Select',
				'label': 'Unidad',
				'options': [" "].concat(uoms_list),
				'reqd': 1
			},
		],
		function(values){
			var index = uoms_list.indexOf(values.uom);
			frm.doc.uom = values.uom;
			frm.doc.conversion_factor = conversion_list[index];
			set_cantidad(frm, frappe);
		},
		'Elige la Unidad de Medida',
		'Ok'
	);
}

frappe.ui.form.on('Toma de Inventario', {

	onload_post_render: function (frm) {
			if (frm.is_new()) {
				frm.set_value("item_table", []);
			}
	},

	validate_item: function(frm){
		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				'doctype': 'Stock Ledger Entry',
				'filters': {
					'item_code': frm.doc.item,
					'warehouse': frm.doc.almacen,
				},
				'fieldname': ['qty_after_transaction']
			},
			callback: function(r){;
				var cantidad = frm.doc.cantidad * parseFloat(frm.doc.conversion_factor);
				for(var i = 0; i < frm.doc.item_table.length; i++){
					if(frm.doc.item_table[i].item === frm.doc.item){
						cantidad += frm.doc.item_table[i].cantidad;
						break;
					}
				}
				if(r.message){
					if(r.message.qty_after_transaction <= 0){
						frappe.msgprint("Item no existe en almacen", "Error");
						frm.set_value('barcode', null);
					}else if(r.message.qty_after_transaction < cantidad){
						frappe.msgprint("Excede existencia en Almacen", "Error");
						frm.set_value('barcode', null);
					}else{
						frappe.call({
							method: 'frappe.client.get_value',
							args: {
								'doctype': 'Item',
								'filters': {
									'item_code': frm.doc.item
								},
								'fieldname': ['item_type', 'insumo']
							},
							callback: function(r){
								if(r.message){
									if(r.message.item_type !== "SKU"){
										frappe.msgprint("Item no es SKU", "Error");
										frm.set_value('barcode', null);
									}else if(!r.message.insumo){
										frappe.msgprint("Item no tiene Insumo Definido", "Error");
										frm.set_value('barcode', null);
									}else{
										frm.doc.insumo = r.message.insumo;
										if(frm.doc.tipo_toma === "Inventario Diario"){
											frappe.call({
												method: 'frappe.client.get_value',
												args: {
													'doctype': 'Item',
													'filters': {
														'item_code': frm.doc.insumo
													},
													'fieldname': ['insumo_diario']
												},
												callback: function(r){
													if(r.message.insumo_diario === 0){
														frappe.msgprint("Item no es Insumo Diario", "Error");
														frm.set_value('barcode', null);
													}else{
														frm.trigger("add_toma");
													}
												}
											});
										}else{
											frm.trigger("add_toma");
										}
									}
								}else{
									frappe.msgprint("Item no Existe", "Error");
									frm.set_value('barcode', null);
								}
							}
						});
					}
				}else{
					frappe.msgprint("No Existe Registro de Item en este Almacen", "Error");
					frm.set_value('barcode', null);
				}
			}
		});
	},


	onload: function(frm){
		var d = new Date();
		if(d.getDay() !== 1){
			frm.set_value("tipo_toma", "Inventario Fisico");
			frm.trigger("set_almacenes");
		}else{
			frm.set_value("tipo_toma", "Inventario Diario");
			frm.trigger("set_almacenes");
		}
	},

	set_almacenes: function(frm){
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				'doctype': 'Warehouse',
				'filters': {'parent_warehouse': 'QSR - H'},
				'fieldname': ['warehouse_name']
			},
			callback: function(r){
				frm.set_df_property('almacen', 'options',(
					function(){
						var array = [" "];
						for(var i = 0; i < r.message.length; i++){
							array.push(r.message[i].name);
						}
						return array
					}
				)());
				frm.refresh_field('almacen');
			}
		});
	},

	agregar: function(frm) {
		frm.trigger("validate_item");
	},

	add_toma: function(frm){
		var itemList = [];
		$.each(frm.doc.item_table, function(index, value){
			itemList.push(value.item);
		});
		var i = itemList.indexOf(frm.doc.item);
		if(i !== -1){
			frm.doc.item_table[i].cantidad += frm.doc.cantidad * parseFloat(frm.doc.conversion_factor);
		}else{
			frm.add_child("item_table", {
			 item: frm.doc.item,
			 nombre_item: frm.doc.item_name,
			 unidad: frm.doc.stock_uom,
			 cantidad: frm.doc.cantidad * parseFloat(frm.doc.conversion_factor)
			});
		}
		frm.set_value("last_item", frm.doc.item_name);
		frm.set_value("last_uom", frm.doc.uom);
		frm.set_value("last_cantidad", frm.doc.cantidad);
		frm.set_value("barcode", null);
		frm.refresh_field("item_table");
	},

	cambiar_unidad: function(frm){
		frappe.prompt(
			[
				{
					'fieldname': 'uom',
					'fieldtype': 'Select',
					'label': 'Unidad',
					'options': [" "].concat(uoms_list),
					'reqd': 1
				},
			],
			function(values){
				var index = uoms_list.indexOf(values.uom);
				frm.doc.uom = values.uom;
				frm.doc.conversion_factor = conversion_list[index];
			},
			'Elige la Unidad de Medida',
			'Ok'
		);
	},

	barcode: function(frm){
		if(frm.doc.barcode){
			if(frm.doc.barcode.indexOf(" ") > -1){
				var index = frm.doc.barcode.indexOf(" ") - 1;
				frm.doc.barcode = frm.doc.barcode.substr(2,index);
			}
			frappe.call({
				method: 'frappe.client.get',
				args: {
					'doctype': 'Item',
					'filters': {'barcode': frm.doc.barcode}
				},
				callback: function(r){
					if(r.message){
						if(r.message.grupo_de_conteo === frm.doc.grupo_de_conteo){
							frm.doc.item = r.message.item_code;
							frm.doc.item_name = r.message.item_name;
							set_cantidad(frm, frappe);
						}else{
							frm.doc.grupo_de_conteo = r.message.grupo_de_conteo;
							frm.doc.item = r.message.item_code;
							frm.doc.item_name = r.message.item_name;
							frm.doc.stock_uom = r.message.stock_uom;
							set_unidad(frm, frappe, r.message.uoms);
						}
					}else{
						frappe.msgprint("Codigo de Barra no Valido", "Error");
						frm.set_value("barcode", null);
					}
				}
			});
		}
	}
});
