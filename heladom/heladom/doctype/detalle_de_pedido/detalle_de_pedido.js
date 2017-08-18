// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt
moment.locale('es')
moment().format('LLLL')

// asign the prompt object to this global var
var prmt = undefined

frappe.ui.form.on('Detalle de Pedido', {
	refresh: function(frm) {

		if ( !frm.doc.parent) {
			frm.trigger("pedido_en_linea")
		}

		setTimeout(function() {
			$(".close.btn-open-row").hide() //a pedido de @Jesus Salcie
			$(".data-row.row.sortable-handle").unbind("click") //a pedido de @Jesus Salcie
		}, 500)

		if ( !frm.doc.__islocal) {
			frm.page.menu_btn_group.removeClass("hide")

			frm.add_custom_button(__("Cambiar pedido"), function(data) {
				frm.trigger("pedido_en_linea")
			})
		}
	},
	pedido_en_linea: function(frm) {

		var title = "Pedido en Linea asociado a este Documento"
		var btn = "Continuar"

		var fields = {
			"label": "Pedido en Linea", "fieldname": "pedido_en_linea",
			"fieldtype": "Link", "options": "Pedido en Linea"
		}

		var query = function(){ return { "filters": { "docstatus": "0" } } }

		var callback = function(data) {
			frappe.model.set_value(frm.doctype, frm.docname, "parent", data.pedido_en_linea)
			frm.trigger("fetch_from_pedido")

			// let's clear the prompt
			prmt = undefined
		}

		prmt && prmt.show()
		prmt = prmt || frappe.prompt(fields, callback, title, btn)

		// set the query for the field
		prmt.fields_dict.pedido_en_linea.get_query = query
	},
	onload: function(frm) {
		if (frm.doc.parent) {
			var fields = [
				"date",
				"cost_center",
				"supplier",
				"estimation_type",
				"cut_trend",
				"rotation_key" ]

			$.each(fields, function(key, field) {
				frm.set_df_property(field, "read_only", true)
			})
		}
	},
	onload_post_render: function(frm) {
		frm.doc.original_coverage = flt(frm.doc.coverage_weeks) - flt(frm.doc.cobertura_relativa)
	},
	cobertura_relativa: function(frm) {
		var coverage_weeks = frm.doc.original_coverage + frm.doc.cobertura_relativa
		frm.set_value("coverage_weeks", coverage_weeks)
	},
	fetch_from_pedido: function(frm) {
		if ( !frm.doc.parent){

			// exit code is one
			return 1 // as there's should be a value in the parent's field
		} 

		var method = "frappe.client.get"
		var args = {
			"doctype": "Pedido en Linea",
			"name": frm.doc.parent
		}
		
		var callback = function(response) {
			var doc = response.message

			if ( !doc) {
				frappe.throw("No se encontro el Pedido en Linea!")
			}

			var fields = [ 
				"date", "rotation_key",
				"cost_center", "supplier",
				"estimation_type", "cut_trend"
			]

			$.each(fields, function(key, field) {
				frappe.set_value(field, doc[field])
				frm.set_df_property(field, "read_only", true)
			})
		}

		frappe.call({ "method": method, "args": args, "callback": callback })
	},
	validate: function(frm) {
		// to-do
	},
	after_save: function(frm) {
		if (frm.doc.parent) {
			setTimeout(function(){
				frappe.set_route(["Form", "Pedido en Linea", frm.doc.parent])
			}, 999)
		}
	},
	sku: function(frm) {
		if ( !frm.doc.sku || !frm.doc.date){
			return 0 // exit code is zero
		} 

		frm.call("set_missing_values", "args", function(response) {
			frm.dirty()
		})
	},
	date: function(frm) {
		if ( !frm.doc.date) {
			frm.set_value("date", frappe.datetime.get_today())
		}

		//if not transit weeks then set it to 0
		if ( !frm.doc.transit_weeks) {
			frm.doc.transit_weeks = 8 // to-check
		}

		//trigger the transit weeks event
		frm.trigger("transit_weeks")
	},
	transit_weeks: function(frm) {
		var me = this
		var date = new Date(frm.doc.date)
		var momt = moment(date).utc()

		// add transit weeks in days to the arrival date
		momt.add(frm.doc.transit_weeks * 7, 'days')

		frm.set_value("arrival_date", momt.format("ddd, D MMM YYYY"))
		frm.trigger("coverage_weeks")
	},
	coverage_weeks: function(frm) {
		var date = new Date(frm.doc.date)
		var momt = moment(date).utc()

		// convert transit weeks into days
		var transit_weeks_in_days = frm.doc.transit_weeks * 7

		// convert transit weeks into days
		var consumption_weeks_in_days = frm.doc.consumption_weeks * 7

		// add one day to the date which means it will be started the next day
		momt.add(transit_weeks_in_days +1, 'days')

		frm.set_value("consumption_date", momt.format("ddd, D MMM YYYY"))
		frm.set_value("consumption_weeks", frm.doc.coverage_weeks - frm.doc.transit_weeks)
		
		if ( !frm.doc.consumption_weeks) {
			frm.set_value("consumption_weeks", frm.doc.coverage_weeks - frm.doc.transit_weeks +1)
		}

		// substract the day that was added to the transit weeks
		momt.add(consumption_weeks_in_days -1, 'days')

		frm.set_value("coverage_date", momt.format("ddd, D MMM YYYY"))
	},
	required_qty: function(frm, cdt, cdn) {
		if (frm.doc.required_qty == 1) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_1 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit
		} else if (frm.doc.required_qty == 2) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_2 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit
		} else if (frm.doc.required_qty == 3) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_3 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit
		}

		frm.doc.order_sku_total = flt(frm.doc.order_sku_real_reqd) + flt(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)

		frm.doc.level_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_level)
		frm.doc.pallet_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_pallet)

		refresh_many(["order_sku_real_reqd", "order_sku_total", "level_qty", "pallet_qty"])
	},
	logistica: function(frm, cdt, cdn) {

		frm.doc.order_sku_total = flt(frm.doc.order_sku_real_reqd) + flt(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)
			//frm.doc.order_sku_total = frm.doc.order_sku_total + frm.doc.logistica
		frm.doc.level_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_level)
		frm.doc.pallet_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_pallet)
		refresh_many(["order_sku_total", "level_qty", "pallet_qty"])
	},
	mercadeo: function(frm, cdt, cdn) {
		frm.doc.order_sku_total = flt(frm.doc.order_sku_real_reqd) + flt(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)
			//frm.doc.order_sku_total = frm.doc.order_sku_total + frm.doc.mercadeo

		frm.doc.level_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_level)
		frm.doc.pallet_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_pallet)
		refresh_many(["order_sku_total", "level_qty", "pallet_qty"])
	},
	planta: function(frm, cdt, cdn) {
		frm.doc.order_sku_total = flt(frm.doc.order_sku_real_reqd) + flt(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)
		frm.doc.level_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_level)
		frm.doc.pallet_qty = flt(frm.doc.order_sku_total / frm.doc.piece_by_pallet)
	},
	type_use_period: function(frm, cdt, cdn) {
		if (frm.doc.type_use_period == "Presupuesto General") {
			frm.doc.tendency__use_period = frm.doc.presup_gral
			frm.doc.real_reqd_use_period = flt(frm.doc.total_reqd_use_period + (frm.doc.total_reqd_use_period * frm.doc.presup_gral / 100))
		} else if (frm.doc.type_use_period == "Tendencia") {
			frm.doc.tendency__use_period = frm.doc.tendency
			frm.doc.real_reqd_use_period = flt(frm.doc.total_reqd_use_period + (frm.doc.total_reqd_use_period * frm.doc.tendency / 100))
				//if tendency is negative it will subtract otherwise will add
		}

		frm.doc.reqd_option_3 = flt(frm.doc.real_required + flt(frm.doc.real_reqd_use_period))

		refresh_many(["tendency__use_period", "real_reqd_use_period", "reqd_option_3"])
	},
	type: function(frm, cdt, cdn) {
		if (frm.doc.type == "Presupuesto General") {
			frm.doc.recent_tendency = frm.doc.presup_gral
			frm.doc.real_required = flt(frm.doc.total_required + (frm.doc.total_required * frm.doc.presup_gral / 100))
		} else if (frm.doc.type == "Solo Tend Despacho") {
			frm.doc.recent_tendency = frm.doc.tendency
			frm.doc.real_required = flt(frm.doc.total_required + (frm.doc.total_required * frm.doc.recent_tendency / 100))
		}

		frm.doc.reqd_option_3 = flt(frm.doc.real_required + flt(frm.doc.real_reqd_use_period))

		refresh_many(["recent_tendency", "real_required", "reqd_option_3"])
	},
})

function next_date(date, weeks) {
	var date_with_weeks = add_weeks(date, weeks)

	return {
		"formatted": date_with_weeks.format("ddd, D MMM YYYY"),
		"week_number": date_with_weeks.add(-1, 'days').format("YYYY.W")
	}
}

function add_weeks(date, weeks) {
	return moment(date).add(weeks, "weeks").utc()
}

function format_date(date) {
	return moment(date).utc().format("ddd, D MMM YYYY")
}