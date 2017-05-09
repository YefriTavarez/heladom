// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt
moment.locale('es')
moment().format('LLLL')

frappe.ui.form.on('Detalle de Estimacion', {
	refresh: function(frm) {
		frm.trigger("date")

		if (!frm.doc.parent) {
			frm.trigger("estimacion_de_compra")
		}

		setTimeout(function() {
			$(".close.btn-open-row").hide() //a pedido de @Jesus Salcie
			$(".data-row.row.sortable-handle").unbind("click") //a pedido de @Jesus Salcie
		}, 500)

		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Duplicar"), function(data) {
				frm.copy_doc()
			}, "Menu")

			frm.add_custom_button(__("Cambiar Estimacion"), function(data) {
				frm.trigger("estimacion_de_compra")
			}, "Menu")

			frm.add_custom_button(__("Refrescar"), function(data) {
				frm.reload_doc()
			}, "Menu")

			frm.add_custom_button(__("Nuevo"), function(data) {
				frappe.new_doc(frm.doctype, true)
			}, "Menu")

			if (!frm.doc.docstatus == 1) {
				frm.add_custom_button(__("Eliminar"), function(data) {
					frappe.model.delete_doc(frm.doctype, frm.docname, function(response) {
						if (response) {
							frappe.set_route("List", frm.doctype)
						}
					})
				}, "Menu")
			}
		}
	},
	estimacion_de_compra: function(frm) {
		var callback = function(data) {
			frappe.model.set_value(frm.doctype, frm.docname, "parent", data.estimacion_de_compra)
			frm.trigger("fetch_from_estimacion")
		}

		frappe.prompt({
			"label": "Estimacion de Compras",
			"fieldname": "estimacion_de_compra",
			"fieldtype": "Link",
			"options": "Estimacion de Compras"
		}, callback, "Seleccione la <i>Estimacion de Compra</i> asociada a este Documento.", "Continuar")
	},
	onload: function(frm) {
		if (frm.doc.parent) {
			$.each(["date", "cost_center", "supplier", "estimation_type", "cut_trend"], function(key, field) {
				frm.set_df_property(field, "read_only", 1)
			})
		}

		if (!frm.doc.__islocal) return

		frappe.model.get_value(doctype = "Configuracion", "Configuracion", "weeks", function(data) {
			frm.doc.cut_trend = data.weeks
			refresh_field("cut_trend")
		})

		frappe.model.get_value(doctype = "Configuracion", "Configuracion", "general_percent", function(data) {
			frm.doc.presup_gral = data.general_percent
			refresh_field("presup_gral")
		})
	},
	fetch_from_estimacion: function(frm) {
		if (!frm.doc.parent) return

		frappe.call({
			method: "frappe.client.get",
			args: {
				"doctype": "Estimacion de Compras",
				"name": frm.doc.parent
			},
			callback: function(response) {
				var fields = [
					"date",
					"rotation_key",
					"cost_center",
					"supplier",
					"estimation_type", 
					"cut_trend"
				]

				$.each(fields, function(key, field) {
					frappe.model.set_value(frm.doctype, frm.docname, field, response.message[field])
					frm.set_df_property(field, "read_only", 1)
				})
			}
		})
	},
	validate: function(frm) {
		if (frm.doc.__islocal) return

		validated = false
		frm.doc.needs_to_save = 0
		$c('runserverobj', {
			'method': 'update_parent',
			'docs': frm.doc
		}, function(response) {
			frm.trigger("after_save")
		})
	},
	after_save: function(frm) {
		if (!frappe.route_history) return
		var reversed_history = frappe.route_history.reverse()
		$.each(reversed_history, function(key,history){
			if (history[0] == "Form" && history[1] == "Estimacion de Compras") {
				setTimeout(function(){
					frappe.set_route(history)
				}, 999)
			}
		})

		frm.reload_doc()
	},
	sku: function(frm) {
		if (!frm.doc.sku || !frm.doc.date) return

		$c('runserverobj', {
				'method': 'set_missing_values',
				'docs': frm.doc
			},

			function(response) {
				frappe.model.trigger("*", "*", frm.doc)
				frm.refresh_fields()
			},

			function(response) {
				//frm.doc.sku = undefined
				//refresh_field("sku")
			})
	},
	date: function(frm) {
		//if there is not date then exit the function
		if (!frm.doc.date) {
			frm.doc.date = frappe.datetime.get_today()
			refresh_field("date")
		}

		//if not transit weeks then set it to 0
		if (!frm.doc.transit_weeks) {
			frm.doc.transit_weeks = 8
		}

		//trigger the transit weeks event
		frm.trigger("transit_weeks")
	},
	transit_weeks: function(frm) {
		var me = this
		var date = new Date(frm.doc.date)
		var momt = moment(date).utc()
		momt.add(frm.doc.transit_weeks * 7, 'days')

		frm.doc.arrival_date = momt.format("ddd, D MMM YYYY")
		refresh_many(["arrival_date"])
		frm.trigger("coverage_weeks")
	},
	coverage_weeks: function(frm) {
		var date = new Date(frm.doc.date)
		var momt = moment(date).utc()
		momt.add(frm.doc.transit_weeks * 7 + 1, 'days')

		frm.doc.consumption_date = momt.format("ddd, D MMM YYYY")
		frm.doc.consumption_weeks = frm.doc.coverage_weeks - frm.doc.transit_weeks
		if (!frm.doc.consumption_weeks) {
			frm.doc.consumption_weeks = frm.doc.coverage_weeks - frm.doc.transit_weeks + 1
		}
		refresh_many(["consumption_date", "consumption_weeks"])

		momt.add(frm.doc.consumption_weeks * 7 - 1, 'days')
		frm.doc.coverage_date = momt.format("ddd, D MMM YYYY")

		refresh_many(["coverage_weeks", "coverage_date"])
	},
	required_qty: function(frm, cdt, cdn) {
		if (frm.doc.required_qty == 1) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_1 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit
		} else if (frm.doc.required_qty == 2) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_2 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit
		} else if (frm.doc.required_qty == 3) {
			frm.doc.order_sku_real_reqd = frm.doc.reqd_option_3 - frm.doc.order_sku_existency - frm.doc.order_sku_in_transit
		}

		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)

		frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2)
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2)

		refresh_many(["order_sku_real_reqd", "order_sku_total", "level_qty", "pallet_qty"])
	},
	logistica: function(frm, cdt, cdn) {

		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)
			//frm.doc.order_sku_total = frm.doc.order_sku_total + frm.doc.logistica
		frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2)
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2)
		refresh_many(["order_sku_total", "level_qty", "pallet_qty"])
	},
	mercadeo: function(frm, cdt, cdn) {
		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)
			//frm.doc.order_sku_total = frm.doc.order_sku_total + frm.doc.mercadeo

		frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2)
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2)
		refresh_many(["order_sku_total", "level_qty", "pallet_qty"])
	},
	planta: function(frm, cdt, cdn) {
		frm.doc.order_sku_total = parseFloat(frm.doc.order_sku_real_reqd) + parseFloat(frm.doc.mercadeo + frm.doc.logistica + frm.doc.planta)
		frm.doc.level_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_level).toFixed(2)
		frm.doc.pallet_qty = parseFloat(frm.doc.order_sku_total / frm.doc.piece_by_pallet).toFixed(2)
	},
	type_use_period: function(frm, cdt, cdn) {
		if (frm.doc.type_use_period == "Presupuesto General") {
			frm.doc.tendency__use_period = frm.doc.presup_gral
			frm.doc.real_reqd_use_period = parseFloat(frm.doc.total_reqd_use_period + (frm.doc.total_reqd_use_period * frm.doc.presup_gral / 100)).toFixed(2)
		} else if (frm.doc.type_use_period == "Tendencia") {
			frm.doc.tendency__use_period = frm.doc.tendency
			frm.doc.real_reqd_use_period = parseFloat(frm.doc.total_reqd_use_period + (frm.doc.total_reqd_use_period * frm.doc.tendency / 100)).toFixed(2)
				//if tendency is negative it will subtract otherwise will add
		}

		frm.doc.reqd_option_3 = parseFloat(frm.doc.real_required + parseFloat(frm.doc.real_reqd_use_period)).toFixed(0)

		refresh_many(["tendency__use_period", "real_reqd_use_period", "reqd_option_3"])
	},
	type: function(frm, cdt, cdn) {
		if (frm.doc.type == "Presupuesto General") {
			frm.doc.recent_tendency = frm.doc.presup_gral
			frm.doc.real_required = parseFloat(frm.doc.total_required + (frm.doc.total_required * frm.doc.presup_gral / 100)).toFixed(2)
		} else if (frm.doc.type == "Solo Tend Despacho") {
			frm.doc.recent_tendency = frm.doc.tendency
			frm.doc.real_required = parseFloat(frm.doc.total_required + (frm.doc.total_required * frm.doc.recent_tendency / 100)).toFixed(2)
		}

		frm.doc.reqd_option_3 = parseFloat(frm.doc.real_required + parseFloat(frm.doc.real_reqd_use_period)).toFixed(0)

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