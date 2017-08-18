// Copyright (c) 2016, Soldeva SRL and contributors
// For license information, please see license.txt

frappe.provide("heladom.fisico")

frappe.ui.form.on('Inventario Fisico Helados', {
	refresh: function(frm) {
		frm.set_query("sku", "items", function() {
			return {
				"filters": {
					"item_group": "Refrigerado Int"
				}
			}
		})
	},
	onload_post_render: function(frm) {
		heladom.fisico.skus = new Array()

		$.each(frm.doc.items || [], function(idx, row) {

			var method = "frappe.client.get"
			var args = {
				"doctype": "Item",
				"name": row.sku
			}

			var callback = function(response) {
				var item_doc = response.message

				heladom.fisico.skus.push(item_doc)
			}

			frappe.call({ "method": method, "args": args, "callback": callback })
		})
	}
})

frappe.ui.form.on('Inventario Fisico Helados Items', {
	sku: function(frm, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn)

		if ( !row.sku) {
			return 0 // exit code is zero
		}

		heladom.fisico.get_sku(frm, cdt, cdn)
	},
	tubo_qty: function(frm, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn)
		var item_doc = heladom.fisico.find_sku(row)

		if ( !item_doc) {
			heladom.fisico.get_sku(frm, cdt, cdn)
		} else {
			var onces_total = heladom.fisico.calculate(row, item_doc)
			frappe.model.set_value(cdt, cdn, "onces_total", onces_total)
		}
	},
	pul_qty: function(frm, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn)
		var item_doc = heladom.fisico.find_sku(row)

		if ( !item_doc) {
			heladom.fisico.get_sku(frm, cdt, cdn)
		} else {
			var onces_total = heladom.fisico.calculate(row, item_doc)
			frappe.model.set_value(cdt, cdn, "onces_total", onces_total)
		}
	},
	onces_qty: function(frm, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn)
		var item_doc = heladom.fisico.find_sku(row)

		if ( !item_doc) {
			heladom.fisico.get_sku(frm, cdt, cdn)
		} else {
			var onces_total = heladom.fisico.calculate(row, item_doc)
			frappe.model.set_value(cdt, cdn, "onces_total", onces_total)
		}
	}
})

$.extend(heladom.fisico, {
	get_sku: function(frm, cdt, cdn) {
		var me = this
		var row = frappe.get_doc(cdt, cdn)

		var method = "frappe.client.get"
		var args = {
			"doctype": "Item",
			"name": row.sku
		}

		var callback = function(response) {
			var item_doc = response.message

			me.skus.push(item_doc)

			me.calculate(row, item_doc)
		}

		var item_doc = me.find_sku(row)

		if (item_doc) {
			var onces_total = me.calculate(row, item_doc)
			frappe.model.set_value(cdt, cdn, "onces_total", onces_total)
		} else {
			frappe.call({ "method": method, "args": args, "callback": callback })
		}
	},
	find_sku: function(row) {
		var me = this
		var sku_found = null

		$.each(me.skus, function(idx, sku) {
			if (sku.name == row.sku) {
				sku_found = sku
			}
		})

		return sku_found
	},
	calculate: function(row, sku) {
		var me = this
		me.current_sku = sku
		me.current_row = row

		var onzas_total = 0.000

		if (row.tubo_qty) {
			onzas_total += flt(row.tubo_qty) * flt(me.get_rate(from="Tub", to="Onzas"))
		}

		if (row.pul_qty) {
			onzas_total += flt(row.pul_qty) * flt(me.get_rate(from="Pulgadas", to="Onzas"))
		}

		if (row.onces_qty) {
			onzas_total += flt(row.onces_qty) * flt(me.get_rate(from="Onzas", to="Onzas"))
		}

		return onzas_total
	},
	get_rate: function(from, to) {
		var me = this
		var sku = me.current_sku
		var rate = 0.000

		$.each(sku.conversion_factors, function(idx, row) {
			if (row.from_uom == from && row.to_uom == to) {
				rate = row.conversion_factor
			}
		})

		if ( !rate) {
			frappe.throw(__("SKU {0} no tiene definido la conversion desde {0} a {1}", 
				[sku.name, from, to]))
		}

		return rate
	}
})
