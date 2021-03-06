// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Estimacion de Compras', {
	refresh: function(frm) {

		if ( ! frm.doc.__islocal) {
			frm.page.menu_btn_group.removeClass("hide")
		}

		frm.trigger("refresh_triggers")
	},
	onload: function(frm) {

	},
	onload_post_render: function(frm) { // check for new status field
		var doctype = "Purchase Order"
		var fields = ["name"]
		var filters = {
			"created_from": frm.docname,
			"docstatus": ["!=", "2"]
		}

		var callback = function(data) {
			frm.doc.has_purchase_order = !! data
		}

		frappe.db.get_value(doctype, filters, fields, callback)
	},
	setup: function(frm) {
		if ( ! (frm.doc.date || frm.doc.docstatus)) {

			frm.doc.sku_list_prompt = undefined
			frm.doc.date_picker_prompt = undefined
		}
	},
	refresh_triggers: function(frm) {

		frm.trigger("set_queries")
		frm.trigger("existe_orden_de_compra")

		if ( ! frm.doc.__islocal) {
			frm.trigger("paint_detalles_estimacion")
		} else {
			// hide the button
			frm.set_df_property("crear_estimaciones", "hidden", "true")
		}

		frm.set_df_property("date", "read_only", !! frm.doc.date)
	},
	date: function(frm) {
		var today = frm.doc.date

		// if there is not date then exit the function
		if ( ! today) {

			return 1.000
		} 

		frappe.call({
			"method": "heladom.api.validate_estimation_date",
			"args": {
				"date": frm.doc.date
			},
			"error": function(response) {
				setTimeout(function() {
					frm.doc.date = undefined
					refresh_field("date")
				}, 999)
			}
		})

		var last_year = frappe.datetime.add_months(today, -12)

		frm.set_value("start_date", last_year)
		frm.set_value("end_date", today)
	},
	supplier: function(frm) {
		if ( ! frm.doc.date) {
			frm.doc.date = frappe.datetime.get_today()
		}

		var doctype = "Supplier"
		var docname = frm.doc.supplier
		var fields = {
			"historia_reciente": "cut_trend",
			"transito": "transit_weeks",
			"cobertura": "coverage_weeks",
			"prevision_minima": "presup_gral",
			"keys": function() {
				var fields = []

				$.each(this, function(key, value) {
					key != "keys" && fields.push(key)
				})

				return fields
			}
		}

		var callback = function(data) {
			$.each(data, function(idx, value) {
				frm.set_value(fields[idx], value)
			})

			frm.trigger("date")
		}

		frappe.db.get_value(doctype, docname, fields.keys(), callback)
	},
	transit_weeks: function(frm) {
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
		if ( ! frm.doc.consumption_weeks) {
			frm.doc.consumption_weeks = frm.doc.coverage_weeks - frm.doc.transit_weeks + 1
		}
		refresh_many(["consumption_date", "consumption_weeks"])

		momt.add(frm.doc.consumption_weeks * 7 - 1, 'days')
		frm.doc.coverage_date = momt.format("ddd, D MMM YYYY")

		refresh_many(["coverage_weeks", "coverage_date"])
	},
	crear_estimaciones: function(frm) {

		if (frm.doc.__islocal) {
			frappe.throw("¡Guarde el documento para poder continuar!")
		}

		frappe.call({
			"freeze": true,
			"freeze_message": "Espere...",
			"method": "crear_estimaciones",
			"doc": frm.doc,
			"callback": function(response) {
				frm.reload_doc()
			},
		})
	},
	agregar_estimacion: function(frm) {
		if (frm.doc.__islocal) {
			frappe.throw("¡Guarde el documento para poder continuar!")
		}

		var btn = "Continuar"
		var title = "Listado Genericos"
		var sku_field = {
			"label": "Generico",
			"fieldname": "sku",
			"fieldtype": "Link",
			"reqd": "1",
			"options": "Generico"
		}

		var callback = function(data) {

			var _method = "crear_estimacion"
			var _args = {
				"generico": data.sku
			}

			var _callback = function(response) {

				var doc = frappe.model.sync(response.message)[0]
				var form = "Form"

				var doctype = doc.doctype
				var docname = doc.name

				setTimeout(function() {
					frappe.set_route(form, doctype, docname)
				})
			}

			// clear the prompt
			frm.doc.sku_list_prompt = undefined

			// and finally make the server call
			frm.call(_method, _args, _callback)
		}

		frm.doc.sku_list_prompt && frm.doc.sku_list_prompt.show()
		frm.doc.sku_list_prompt = frm.doc.sku_list_prompt || frappe.prompt(sku_field, callback, title, btn)

		// set the query for the field
		var query_func = function() {
			var filters = {
				// "item_type": "SKU"
			}

			if (frm.doc.estimation_type) {
				$.extend(filters, {
					"item_group": frm.doc.estimation_type
				})
			}

			return {
				"filters": filters
			}
		}

		frm.doc.sku_list_prompt.fields_dict.sku.get_query = query_func
	},
	existe_orden_de_compra: function(frm) {

		if ( ! frm.doc.docstatus == 1) {
			return 0 // exit code is zero
		}

		var doctype = "Purchase Order"
		var fields = ["name"]

		var filters = {
			"created_from": frm.docname,
			"docstatus": ["!=", "2"]
		}

		var callback = function(data) {

			if (data) {
				frm.add_custom_button("Ver Orden", function(event) {
					frappe.set_route("Form", doctype, data.name)
				})

				return 0 // exit code is zero
			}

			var _label = "Crear Orden"
			var _onclick = function(event) {

				var _method = "heladom.api.crear_orden_de_compra"
				var _args = {
					"source": frm.docname
				}

				var _callback = function(response) {
					var new_doc = response.message

					if (new_doc) {
						var doc = frappe.model.sync(new_doc)[0]

						var form = "Form"
						var doctype = doc.doctype
						var docname = doc.name

						frappe.set_route(form, doctype, docname)
					}
				}

				frappe.call({
					"method": _method,
					"args": _args,
					"callback": _callback
				})
			}

			frm.add_custom_button(_label, _onclick)
		}

		frappe.db.get_value(doctype, filters, fields, callback)
	},
	paint_detalles_estimacion: function(frm) {

		var method = "frappe.client.get_list"
		var args = {
			"doctype": "Detalle de Estimacion",
			"filters": {
				"parent": ["=", frm.docname],
				"docstatus": ["!=", "2"]
			},
			"fields": ["name", "date", "sku", "sku_name",
				"current_year_avg", "logistica", "mercadeo",
				"planta", "consumption_weeks", "order_sku_total",
				"level_qty", "pallet_qty"
			],
			"order_by": "name",
			"limit_page_length": "0"
		}

		var callback = function(response) {

			var doc_list = response.message

			var level_qty = 0.000
			var pallet_qty = 0.000

			// if there was an error or if the document has not rows
			if ( ! (doc_list && doc_list.length)) {

				// then let's set the no data message to the table
				frm.doc.html_table = repl(frm.html_table, {
					"empty_message": frm.html_no_data,
					"rows": ""
				})

				// and show the button so that the user can create fill the table using the filters
				frm.set_df_property("crear_estimaciones", "hidden", false)
			}

			// if something was found in the server
			if (doc_list && doc_list.length) {

				var html_rows = new String("")

				// let's iterate the document list to fill the table
				$.each(doc_list, function(idx, current) {
					html_rows += frm.get_new_html_row({
						"idx": idx + 1,
						"cierre": current.date,
						"codigo": current.name,
						"item_code": current.sku,
						"item_name": current.sku_name,
						"promedio": current.current_year_avg,
						"prevision": flt(current.logistica) + flt(current.mercadeo) + flt(current.planta),
						"orden": current.order_sku_total,
						"duracion": current.consumption_weeks,
					})

					level_qty += flt(current.level_qty)
					pallet_qty += flt(current.pallet_qty)
				})

				frm.doc.html_table = repl(frm.html_table, {
					"empty_message": "",
					"footer_display": frm.doc.docstatus == "0" ? "block" : "none",
					"rows": html_rows,
				})

				$.each(["presup_gral", "codigo", "cut_trend"], function(idx, field) {
					frm.set_df_property(field, "read_only", true)
				})

				// frm.doc.level_qty = level_qty
				// frm.doc.pallet_qty = pallet_qty
				frm.fields_dict.level_qty.$wrapper.find(".control-value.like-disabled-input").text(level_qty)
				frm.fields_dict.pallet_qty.$wrapper.find(".control-value.like-disabled-input").text(pallet_qty)

				frm.set_df_property("crear_estimaciones", "hidden", true)
			}

			frm.set_df_property("detalle_table", "options", frm.doc.html_table)
		}

		frappe.call({
			"method": method,
			"args": args,
			"callback": callback
		})
	}
})