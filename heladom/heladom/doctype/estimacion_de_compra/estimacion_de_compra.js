// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt
moment.locale('en');
moment().format('LLLL');

frappe.ui.form.on('Estimacion de Compra', {
	onload: function(frm) {
		if (! frm.doc.__islocal) return ;

		if (frappe.user.has_role("heladom_cost_center_admin") && frappe.session.user != "Administrator") {
            
			frappe.call({
				method: "heladom.heladom.doctype.centro_de_costo.centro_de_costo.get_cost_center_info",
				args: {
					"cost_center_admin": frappe.user.name
				},
	            callback: function (data) {
	                var cost_center = data.message;
	                if(!cost_center.code) return;

	                frm.doc.supplier = "Almacen";
	                frm.doc.cost_center = cost_center.code;
	                frm.doc.is_warehouse_transfer = 1;

		            frm.set_df_property("supplier", "read_only", 1);
		            frm.set_df_property("cost_center", "read_only", 1);
		            frm.set_df_property("is_warehouse_transfer", "read_only", 1);

	                refresh_many(["cost_center","supplier","is_warehouse_transfer"]);
	            }
			});
		}

		frappe.call({
			method: "heladom.heladom.doctype.configuracion.configuracion.get_configuration_info",
			no_spinner: false,
            callback: function (data) {
                var config = data.message;
                if(!config) return;
                
                frm.doc.presup_gral = config.general_percent;
                frm.doc.cut_trend = config.weeks;
	            refresh_many(["cut_trend","presup_gral"]);

            }
		});
		setTimeout(function(){ 
			//if(frm.doc.__islocal)
				//frm.set_intro("Sugerimos elegir Fechas que sean Lunes para optimos resultados.");

			frm.script_manager.trigger("date");
		}, 500);

		console.warn("event onload triggered!");
	},
	sku: function(frm){
		if(! frm.doc.sku || ! frm.doc.date)	return ;

		var callback = function(response){
			frm.refresh();
		};

		frm.clear_table("current_period_table");
		frm.clear_table("previous_period_table");
		frm.clear_table("transit_period_table");
		frm.clear_table("usage_period_table");
		
		$c('runserverobj', args = { 'method': 'set_missing_values', 'docs': frm.doc } , callback);
		console.warn("event sku triggered!");
	},
	date: function(frm){
		//if there is not date then exit the function
		if(!frm.doc.date){
			frm.doc.date = frappe.datetime.get_today();
			refresh_field("date");
		}

		//if not transit weeks then set it to 0
		if(!frm.doc.transit_weeks){
			frm.doc.transit_weeks = 0;
		}

		var date_obj_js = new Date(frm.doc.date);
		var iso_start_of_week = moment(date_obj_js).utc().startOf('isoWeek'); //Monday

	    frm.doc.current_date = iso_start_of_week.format("YYYY.W");
	    frm.doc.sku = undefined;

	    //trigger the transit weeks event
	    frm.trigger("transit_weeks");
		console.warn("event date triggered!");
	},
	transit_weeks: function(frm){
		var transit_weeks = frm.doc.transit_weeks;
		var date_obj_js = new Date(frm.doc.date);
		var cut_trend_date = moment(date_obj_js);
		var date = next_date(cut_trend_date, transit_weeks);

		frm.doc.arrival_date = date.formatted;
		frm.doc.arrival_week = date.week_number;
		refresh_many(["arrival_date", "arrival_week", "consumption_week"]);		
		frm.trigger("consumption_weeks");
		console.warn("event transit_weeks triggered!");
	},
	consumption_weeks: function(frm){
		var consumption_date = moment(new Date(frm.doc.arrival_date)).utc().add(1, "days");

		var formatted_date = format_date(consumption_date);

		frm.doc.consumption_date = formatted_date;
		frm.doc.consumption_week = consumption_date.format("YYYY.W");
		frm.doc.coverage_weeks = flt(frm.doc.consumption_weeks) + flt(frm.doc.transit_weeks);
		refresh_many(["coverage_weeks", "consumption_date", "consumption_week"]);		
		frm.trigger("coverage_weeks");
		console.warn("event consumption_weeks triggered!");
	},
	coverage_weeks: function(frm){
		var diff = flt(frm.doc.coverage_weeks) - flt(frm.doc.transit_weeks);
		frm.doc.consumption_weeks = diff;

		var consumption_week = frm.doc.consumption_weeks;
		var date_obj_js = new Date(frm.doc.arrival_date);
		var consumption_date = moment(date_obj_js);

		var date = next_date(consumption_date, consumption_week);

		frm.doc.coverage_date = date.formatted;
		frm.doc.coverage_week = date.week_number;

		var formatted_date = format_date(consumption_date.add(1, "days"));

		frm.doc.consumption_date = formatted_date;
		frm.doc.consumption_week = consumption_date.format("YYYY.W");
		
		refresh_many(["consumption_weeks", "coverage_date", "coverage_week", "consumption_date", "consumption_week"]);		
		console.warn("event coverage_weeks triggered!");
	},
	required_qty: function(frm, cdt, cdn){
		if (frm.doc.required_qty == 1) {
        	frm.doc.order_sku_real_reqd = frm.doc.reqd_option_1 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit;
		} else if (frm.doc.required_qty == 2) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_2 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit;
		} else if (frm.doc.required_qty == 3) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_3 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit;
		}

		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta);

    	frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2);
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2);
		
		refresh_many(["order_sku_real_reqd","order_sku_total","level_qty","pallet_qty"]);
		console.warn("event required_qty triggered!");
	},
	logistica: function(frm, cdt, cdn){

		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta);
		//frm.doc.order_sku_total = frm.doc.order_sku_total + frm.doc.logistica;
		frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2);
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2);
		refresh_many(["order_sku_total","level_qty","pallet_qty"]);
		console.warn("event triggered!");
	},
	mercadeo: function(frm, cdt, cdn){
		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta);
		//frm.doc.order_sku_total = frm.doc.order_sku_total + frm.doc.mercadeo;

		frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2);
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2);
		refresh_many(["order_sku_total","level_qty","pallet_qty"]);
		console.warn("event logistica triggered!");
	},
	planta: function(frm, cdt, cdn){
		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta);
		frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2);
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2);
		console.warn("event planta triggered!");
	},
	type_use_period: function(frm, cdt, cdn){
		if (frm.doc.type_use_period == "Presupuesto General") {
			frm.doc.tendency__use_period = frm.doc.presup_gral;
			frm.doc.real_reqd_use_period = parseFloat(frm.doc.total_reqd_use_period + (frm.doc.total_reqd_use_period * frm.doc.presup_gral / 100)).toFixed(2);
		} else if(frm.doc.type_use_period == "Tendencia") {
			frm.doc.tendency__use_period = frm.doc.tendency;
			frm.doc.real_reqd_use_period = parseFloat(frm.doc.total_reqd_use_period + (frm.doc.total_reqd_use_period * frm.doc.tendency / 100)).toFixed(2);
			//if tendency is negative it will subtract otherwise will add
		}

		frm.doc.reqd_option_3 = parseFloat(frm.doc.real_required + parseFloat(frm.doc.real_reqd_use_period)).toFixed(0);
				
		refresh_many(["tendency__use_period","real_reqd_use_period","reqd_option_3"]);
		console.warn("event type_use_period triggered!");
	},
	type: function(frm, cdt, cdn){
		if (frm.doc.type == "Presupuesto General") {
			frm.doc.recent_tendency = frm.doc.presup_gral;
			frm.doc.real_required = parseFloat(frm.doc.total_required + (frm.doc.total_required * frm.doc.presup_gral / 100)).toFixed(2);
		} else if(frm.doc.type == "Solo Tend Despacho") {
			frm.doc.recent_tendency = frm.doc.tendency;
			frm.doc.real_required = parseFloat(frm.doc.total_required + (frm.doc.total_required * frm.doc.recent_tendency / 100)).toFixed(2);
		}

		frm.doc.reqd_option_3 = parseFloat(frm.doc.real_required + parseFloat(frm.doc.real_reqd_use_period)).toFixed(0);
				
		refresh_many(["recent_tendency","real_required","reqd_option_3"]);
		console.warn("event type triggered!");
	},
});

function next_date(date, weeks){
	var date_with_weeks = add_weeks(date, weeks);

	return {
		"formatted" : date_with_weeks.format("ddd, D MMM YYYY"),
		"week_number" : date_with_weeks.add(-1,'days').format("YYYY.W")
	}
}

function add_weeks(date, weeks){
	return moment(date).add(weeks, "weeks").utc();
}

function format_date(date){
	return moment(date).utc().format("ddd, D MMM YYYY");
}


function $c(command, args, callback, error, no_spinner, freeze_msg, btn) {
	return frappe.request.call({
		type: "POST",
		args: $.extend(args, {cmd: command}),
		success: callback,
		error: error,
		btn: btn,
		freeze: freeze_msg,
		show_spinner: !no_spinner
	})
}