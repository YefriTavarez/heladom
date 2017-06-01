// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

moment.locale('es')
moment().format('LLLL')

frappe.ui.form.on('Estimacion de Compras', {
	setup: function(frm){
		setTimeout(function() {
			var add_row_button = $(".btn.btn-xs.btn-default.grid-add-row")
			add_row_button.unbind() // to remove the default events
			add_row_button.on("click", function(event) {
				frm.trigger("agregar_estimacion")
			})
		},500)
	},
	refresh: function(frm) {

		if (!frm.doc.__islocal) {
			$.each(["presup_gral", "codigo"], function(idx, field) {
				frm.set_df_property(field, "read_only", frm.doc.items.length? 0: 1)
			})

			frm.set_df_property("crear_estimaciones", "hidden", frm.doc.items.length? 1: 0)

			frm.add_custom_button(__("Refrescar"), function(data) {
				frm.reload_doc()
			}, "Menu")

			frm.add_custom_button(__("Nuevo"), function(data) {
				frappe.new_doc(frm.doctype, true)
			}, "Menu")

			frm.add_custom_button(__("Eliminar"), function(data) {
				frappe.model.delete_doc(frm.doctype, frm.docname, function(response) {
					if (response) {
						frappe.set_route("List", frm.doctype)
					}
				})
			}, "Menu")
		}

		frappe.db.get_value(frm.doctype, frm.docname, "modified", function(data){
			if(frm.doc.__islocal || frm.doc.modified == data.modified) return
			setTimeout(function(){ frm.reload_doc() }, 1000)
		})

		frm.trigger("existe_orden_de_compra")
	},
	onload: function(frm) {
		setTimeout(function() {
			//$(".row-index.col.col-xs-1").hide()
			//$(".close.btn-open-row").hide() //a pedido de @Jesus Salcie

			frm.trigger("date")

			$(".data-row.row.sortable-handle").unbind("click")
			$(".static-area.ellipsis").last().hide()
			$(".btn.btn-xs.btn-default.grid-add-row").text("Agregar Fila")
		}, 100)

	},
	codigo: function(frm) {
		if (frm.doc.__islocal && frm.doc.codigo) {
			//frm.set_intro("Guarde el documento para poder continuar!")
			frm.save()
		}
	},
	date: function(frm) {
		//if there is not date then exit the function
		if (!frm.doc.date) {
			frm.doc.date = frappe.datetime.get_today()
			refresh_field("date")
		}

		var date_obj = new Date(frm.doc.date)
		var moment_obj = moment(date_obj).utc()

		frm.doc.start_date = frappe.datetime.add_months(frm.doc.date, -12)
		frm.doc.end_date = frm.doc.date

		//if not transit weeks then set it to 0
		if (!frm.doc.transit_weeks) {
			frm.doc.transit_weeks = 0
		}

		var date_obj_js = new Date(frm.doc.date)
		var iso_start_of_week = moment(date_obj_js).utc().startOf('isoWeek') //Monday

		//frm.doc.sku = undefined

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
	crear_estimaciones: function(frm) {

		// freeze the screen so the user can get
		// to know that its request is being processed
		frappe.dom.freeze("Espere...")


		var callback = function(response) {
			// exit the function if nothing 
			// is sent back from the server
			if (!response) return

			//frappe.model.trigger("*", "*", frm.doc) //to trigger the unsaved status
			frm.reload_doc()
			frappe.dom.unfreeze()
		}

		$c('runserverobj', { 'method': 'crear_estimaciones', 'docs': frm.doc }, callback)

		frm.set_df_property("crear_estimaciones", "hidden", 1)
	},
	agregar_estimacion: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn]
		var callback = function(response) {
			var data = response.message

			row.cierre = frm.doc.date
			row.codigo = frm.doc.codigo
			row.descripcion = data.sku + " " + data.sku_name
			row.promedio = 0
			row.prevision = 0
			row.orden = 0
			row.duracion = 0

			frappe.set_route("Form", "Detalle de Estimacion", data.name)
			refresh_field("items")
		}

		var sku_field = {
			"label": "SKU",
			"fieldname": "sku",
			"fieldtype": "Link",
			"options": "Item"
		}

		frappe.prompt(sku_field, function(data) {
			if (!data.sku) return

			frm.doc.sku = data.sku
			$c('runserverobj', {'method': 'crear_estimacion', 'docs': frm.doc }, callback)
		},
		"Listado SKU", "Continuar")

	},
	existe_orden_de_compra: function(frm) {
		if (!frm.doc.docstatus == 1) return

		frappe.call({
			method: "heladom.api.existe_orden_de_compra",
			args: {
				"estimacion": frm.docname
			},
			callback: function(response) {
				if (response.message) {
					frm.add_custom_button("Ver Orden", function(event) {
						frappe.set_route("Form", "Orden de Compra", response.message)
					})
				} else {
					frm.add_custom_button("Crear Orden", function(event) {
						frappe.call({
							method: "heladom.api.crear_orden_de_compra",
							args: {
								"est_name": frm.docname
							},
							callback: function(response) {
								if (response.message) {
									doc = frappe.model.sync(response.message)[0]
									frappe.set_route("Form", doc.doctype, doc.name)
								}
							}
						})
					})
				}
			}
		})

	},
})


frappe.ui.form.on("Estimacion de Compra Hijo", {
	onload: function(frm) {
		setTimeout(function() {
			$(".row-index.col.col-xs-1").hide()
		}, 500)
	},
	items_remove: function(frm, cdt, cdn) {
		var callback = function(response){
			$.each(response.message, function(idx, value) {
				frappe.show_alert(
					repl("Detalle <i>%(estimacion)s</i> ha sido eliminada",{"estimacion": value})
				)
			})
			frm.reload_doc()
		};

		$c('runserverobj', {'method': 'remove_complement', 'docs': frm.doc }, callback)
	},
	ver_detalle: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn]

		frappe.route_options = {
			"needs_to_save": true
		}

		frappe.set_route("Form", "Detalle de Estimacion", row.codigo)
	}
})
