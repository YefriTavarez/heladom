// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt
moment.locale('es');
localLocale = moment()
localLocale.format('LLLL');

frappe.ui.form.on('Estimacion de Compra', {
	refresh: function(frm) {

		if (frm.doc.__islocal) {

			if (frappe.user.has_role("heladom_cost_center_admin")) {
				frappe.call({
					"method": "heladom.heladom.doctype.centro_de_costo.centro_de_costo.get_cost_center_info",
					args: {
						"cost_center_admin": frappe.user.name
					},
		            callback: function (data) {
		                var cost_center = data.message;

		                frappe.model.set_value(frm.doctype,
		                    frm.docname, "cost_center", cost_center.code);

		                frappe.model.set_value(frm.doctype,
		                    frm.docname, "supplier", "Almacen");

		                frappe.model.set_value(frm.doctype,
		                    frm.docname, "is_warehouse_transfer", 1);

		                cur_frm.set_df_property("cost_center", "read_only", 1)
		                cur_frm.set_df_property("supplier", "read_only", 1)
		                cur_frm.set_df_property("is_warehouse_transfer", "read_only", 1)
		            }
				});
			}

			frappe.call({
				"method": "heladom.heladom.doctype.configuracion.configuracion.get_configuration_info",
	            callback: function (data) {
	                var config = data.message;

	                frappe.model.set_value(frm.doctype,
	                    frm.docname, "presup_gral", config.general_percent);

	                frappe.model.set_value(frm.doctype,
	                    frm.docname, "cut_trend", config.weeks);
	            }
			});

		}
	},
	before_submit: function(frm){
		// validated = false;
		// if (frm.doc.is_warehouse_transfer) {
		// 	frappe.call({
	 //        	"method": "heladom.heladom.doctype.administrador_de_pedidos.administrador_de_pedidos.METODO",
	 //        	args: {
	 //                "doc": frm.doc
	 //            },
  //       		callback: function (data) {
  //       			console.log(data);
  //       		}
	 //        });
		// }
		// frappe.confirm(
		//     'Deseas crear una Orden de Compra basada en esta estimacion?',
		//     function(){

		//         frappe.call({
		//         	"method": "heladom.heladom.doctype.orden_de_compra.orden_de_compra.add_new_orden_de_compra",
		//         	args: {
		//                 "estimation": frm.doc.name,
		//                 "estimation_date": frm.doc.date,
		//                 "estimation_supplier": frm.doc.supplier
		//             },
  //           		callback: function (data) {
  //           			console.log(data);
  //           		}
		//         });
		//     },
		//     function(){
		//     	cur_frm.save("Submit");
		//         window.close()
		//     }
		// )
	},
	transit: function(frm){
		var transit_weeks = frm.doc.transit;
		var cut_trend_date = moment(frm.doc.date);
		var me = this;
		var date = getNextDateObject(cut_trend_date, transit_weeks);

		frappe.model.set_value(frm.doctype,
                    frm.docname, "date_transit", date.formattedDate);

		frappe.model.set_value(frm.doctype,
                    frm.docname, "transit_week", date.weekOfYear);

	},
	consumption: function(frm){
		var consumption_week = frm.doc.consumption;
		var date_consumption = moment(frm.doc.date_transit).utc().add(1, "days");

		var dateFormatted = date_consumption.format("ddd, D MMM YY");

		frappe.model.set_value(frm.doctype,
                    frm.docname, "date_consumption", dateFormatted);

		frappe.model.set_value(frm.doctype,
                    frm.docname, "consumption_week", date_consumption.year() + "." + date_consumption.isoWeek());

		frappe.model.set_value(frm.doctype,
                    frm.docname, "coverage", frm.doc.consumption + frm.doc.transit);
	},
	coverage: function(frm){
		var consumption_week = frm.doc.consumption;
		var date_consumption = moment(frm.doc.date_consumption);

		var date = getNextDateObject(date_consumption, consumption_week);

		frappe.model.set_value(frm.doctype,
                    frm.docname, "date_coverage", date.formattedDate);

		frappe.model.set_value(frm.doctype,
                    frm.docname, "coverage_week", date.weekOfYear);

	},
	get_estimation_info: function(frm){
		frappe.msgprint("Ejecutando operacion");
		frappe.call({
			"method": "heladom.heladom.doctype.estimacion_de_compra.estimacion_de_compra.get_estimation_info",
            args: {
                doc: frm.doc
            },
            callback: function (data) {
                var skus = data.message;

                if (!skus) return;

                // console.log(data);
                skus.forEach(function(sku){
                	var last_year_avg = sku.last_year_avg;
                	var current_year_avg = sku.current_year_avg;
                	var last_year_transit_avg = sku.last_year_transit_avg;
                	var last_year_consumption_avg = sku.last_year_consumption_avg;

                	var trend = ((current_year_avg / last_year_avg) - 1) * 100;

                	var row = frappe.model.add_child(frm.doc, "estimation_skus");
                	row.sku = sku.code;
                	row.sku_name = sku.item;
                	row.tendency = parseFloat(trend).toFixed(2);
                	row.current_year_avg = parseFloat(current_year_avg).toFixed(2);
                	row.last_year_avg = parseFloat(last_year_avg).toFixed(2);
                	row.desp_avg = parseFloat(last_year_transit_avg).toFixed(2);
                	row.trasit_weeks = frm.doc.transit;
                	row.total_required = row.desp_avg * frm.doc.transit;
                	row.recent_tendency = parseFloat(trend).toFixed(2);
                	row.real_required = row.total_required + (row.total_required *row.recent_tendency /100);
                	row.avg_use_period = parseFloat(last_year_consumption_avg).toFixed(2);
                	row.consumption__use_period = frm.doc.consumption;
                	row.total_reqd_use_period = row.avg_use_period * row.consumption__use_period;
                	row.tendency__use_period = frm.doc.presup_gral;
                	row.real_reqd_use_period = row.total_reqd_use_period + (row.total_reqd_use_period * row.tendency__use_period / 100);

                	row.general_coverage = frm.doc.coverage;
                	row.reqd_option_1 = parseFloat(row.general_coverage * current_year_avg).toFixed(0);
                	row.reqd_option_2 = parseFloat(row.total_required + row.total_reqd_use_period).toFixed(0);
                	row.reqd_option_3 = parseFloat(row.real_required + row.real_reqd_use_period).toFixed(0);
                	row.order_sku_existency = 11;
                	row.order_sku_in_transit = 15;

                	row.order_sku_real_reqd = row.reqd_option_3 - (row.order_sku_existency + row.order_sku_in_transit);
                	row.order_sku_total = row.order_sku_real_reqd;

                	row.piece_by_level = sku.pieces_per_level;
                	row.piece_by_pallet = sku.pieces_per_pallet;

                	row.level_qty = parseFloat(row.order_sku_total / row.piece_by_level).toFixed(2);
					row.pallet_qty = parseFloat(row.order_sku_total / row.piece_by_pallet).toFixed(2);
                });

				cur_frm.refresh();

                frappe.msgprint("El proceso a terminado");
            }
		});
	}
});

frappe.ui.form.on("Estimacion SKUs", {
	required_qty: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if (row.required_qty == 1) {
            row.order_sku_real_reqd = row.reqd_option_1 - (row.order_sku_existency + row.order_sku_in_transit);
		} else if (row.required_qty == 2) {
			row.order_sku_real_reqd = row.reqd_option_2 - (row.order_sku_existency + row.order_sku_in_transit);
		} else if (row.required_qty == 3) {
			row.order_sku_real_reqd = row.reqd_option_3 - (row.order_sku_existency + row.order_sku_in_transit);
		}

		row.order_sku_total = parseFloat(row.order_sku_real_reqd) + parseFloat(row.mercadeo + row.logistica + row.planta);

    	row.level_qty = parseFloat(row.order_sku_total / row.piece_by_level).toFixed(2);
		row.pallet_qty = parseFloat(row.order_sku_total / row.piece_by_pallet).toFixed(2);
		
		frm.refresh_field("estimation_skus");
	},
	logistica: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		row.order_sku_total = row.order_sku_total + row.logistica;
		row.level_qty = parseFloat(row.order_sku_total / row.piece_by_level).toFixed(2);
		row.pallet_qty = parseFloat(row.order_sku_total / row.piece_by_pallet).toFixed(2);
		frm.refresh_field("estimation_skus");
	},
	mercadeo: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		row.order_sku_total = row.order_sku_total + row.mercadeo;

		row.level_qty = parseFloat(row.order_sku_total / row.piece_by_level).toFixed(2);
		row.pallet_qty = parseFloat(row.order_sku_total / row.piece_by_pallet).toFixed(2);
		frm.refresh_field("estimation_skus");
	},
	planta: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		row.order_sku_total = row.order_sku_total + row.planta;
		row.level_qty = parseFloat(row.order_sku_total / row.piece_by_level).toFixed(2);
		row.pallet_qty = parseFloat(row.order_sku_total / row.piece_by_pallet).toFixed(2);
		frm.refresh_field("estimation_skus");
	},
	type: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		console.log(row);
	},
	type_use_period: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];

		if (row.type_use_period == "Presupuesto General") {
			row.tendency__use_period = frm.doc.presup_gral;
			row.real_reqd_use_period = parseFloat(row.total_reqd_use_period + (row.total_reqd_use_period * frm.doc.presup_gral / 100)).toFixed(0);
		} else if(row.type_use_period == "Tendencia") {
			row.tendency__use_period = row.tendency;
			row.real_reqd_use_period = parseFloat(row.total_reqd_use_period + (row.total_reqd_use_period * row.tendency / 100)).toFixed(0);
		}

		row.reqd_option_3 = parseFloat(row.real_required + parseFloat(row.real_reqd_use_period)).toFixed(0);
				
		frm.refresh_field("estimation_skus");
	},
});

function getNextDateObject(date, weeks){
	var newDate = getDateByWeek(date, weeks);
		var formattedDate = getFormattedDateForUser(newDate);
		var week = getWeekOfYear(newDate);
		var year = getYear(newDate);

		return {
			"formattedDate": formattedDate,
			"weekOfYear": year + "." + week
		}
}

function getDateByWeek(date, weeks){
	var newDate = moment(date).add(weeks, "weeks");
	return newDate;
}

function getFormattedDate(date){
	return moment(date).utc().format("ddd, D MM YYYY")
}

function getFormattedDateForUser(date){
	return moment(date).utc().format("ddd, D MMM YY")
}

function getWeekOfYear(date){
	return moment(date).utc().isoWeek();
}

function getYear(date){
	return moment(date).utc().year();
}