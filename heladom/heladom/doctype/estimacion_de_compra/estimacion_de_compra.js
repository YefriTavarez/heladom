// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt
moment.locale('es');
localLocale = moment()
localLocale.format('LLLL');

frappe.ui.form.on('Estimacion de Compra', {
	refresh: function(frm) {

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

		var last_cut = moment().utc();

		frappe.model.set_value(frm.doctype,
                    frm.docname, "date_cut_trend", last_cut.format("ddd, D MMM YY"));

		frappe.model.set_value(frm.doctype,
                    frm.docname, "cut_trend_week", last_cut.year() + "." + last_cut.isoWeek());
	},
	before_submit: function(frm){
		validated = false;
		frappe.confirm(
		    'Deseas crear una Orden de Compra basada en esta estimacion?',
		    function(){

		        frappe.call({
		        	"method": "heladom.heladom.doctype.orden_de_compra.orden_de_compra.add_new_orden_de_compra",
		        	args: {
		                "estimation": frm.doc.name,
		                "estimation_date": frm.doc.date,
		                "estimation_supplier": frm.doc.supplier
		            },
            		callback: function (data) {
            			console.log(data);
            		}
		        });
		    },
		    function(){
		    	cur_frm.save("Submit");
		        window.close()
		    }
		)
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
                doctype: "Library Member"
            },
            callback: function (data) {
                var skus = data.message;
                skus.forEach(function(sku){
                	var row = frappe.model.add_child(frm.doc, "estimation_skus");
                	row.sku = sku.code;
                	row.sku_name = sku.item;
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
		console.log(row);
	},
	logistica: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		console.log(row);
	},
	mercadeo: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		console.log(row);
	},
	planta: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		console.log(row);
	},
	type: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		console.log(row);
	},
	type_use_period: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		console.log(row);
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