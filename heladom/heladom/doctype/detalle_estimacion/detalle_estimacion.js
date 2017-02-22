// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Detalle Estimacion', {
	onload: function(frm){
		frm.trigger("select_stimation");
	},
	refresh: function(frm){
		frm.add_custom_button("Selecionar Estimacion", function(e){
			frm.trigger("select_stimation");
		});

		cur_frm.toolbar.print_icon.addClass("hide");
		cur_frm.disable_save();
	},
	select_stimation: function(frm) {
		estimation_docfield = {
			"label" : "Estimacion de Compra",
			"fieldname" : "estimacion_de_compra", 
			"fieldtype" : "Link", 
			"options" :  "Estimacion de Compra"
		};

		callback = function(response){
			frm.set_query("sku", function() {
				return {
					filters: {
						parent: response.estimacion_de_compra
					}
				}
			});

			frm.fields_dict.sku.$input.focusout();
			frm.doc.sku = "";
			refresh_field("sku");
		}

		frappe.prompt([estimation_docfield], callback, "Seleccione los parámetros", "Continuar");
	},
	sku: function(frm){
		if(! frm.doc.sku){
			return ;
		}

		var success_callback = function(response){
			cur_frm.refresh();
		};

		frm.clear_table("recent_history")
		frm.clear_table("transit_period");
		frm.clear_table("usage_period");
		frm.refresh();
		
		$c('runserverobj', args = { 'method': 'fill_tables', 'docs': cur_frm.doc }, success_callback, console.error, true, "Procesando");
	}
});

var estimacion_docfield = function(e){
	estimation_field = cur_dialog.$wrapper.find("input[data-fieldname=estimacion_de_compra]");

	estimation_field.on("change", function(e){
		value = estimation_field.val();
		cur_frm.set_query("sku", function() {
			return {
				filters: {
					parent: value
				}
			}
		});

		cur_dialog.hide();
	});
};

setTimeout(estimacion_docfield, 1000);