# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt

class PedidoenLinea(Document):

	def crear_pedidos(self):
		"""Create a new  set of Detalle de Pedido based on the current Pedido en Linea filters"""

		for sku in self.listado_skus():

			frappe.errprint("creating pedido {0}".format(sku.name))
			detalle = self.crear_pedido(sku.name)

			detalle.insert()
		frappe.errprint("finished creating pedidos")

	def crear_pedido(self, sku):
		"""Create a new Detalle de Pedido based on the current Pedido en Linea"""

		# allocate a new doc in memory
		detalle = frappe.new_doc("Detalle de Pedido")

		relative_coverage = frappe.get_value("Item", sku, "relative_coverage")

		if self.is_new():
			frappe.throw(msg="¡Pedido en Linea no encontrada!", title="¡Atencion requerida!")

		# setting the header info
		detalle.date = self.date
		detalle.cost_center = self.cost_center
		detalle.supplier = self.supplier
		detalle.cut_trend = self.cut_trend
		detalle.presup_gral = self.presup_gral
		detalle.transit_weeks = self.transit_weeks
		detalle.arrival_date = self.arrival_date
		detalle.consumption_weeks = self.consumption_weeks
		detalle.consumption_date = self.consumption_date
		detalle.coverage_weeks = self.coverage_weeks
		detalle.coverage_date = self.coverage_date
		detalle.parent = self.name
		detalle.sku = sku

		detalle.set_missing_values()

		return detalle


	def listado_skus(self):
		"""Fetch from the Database all the SKU Items that are not disabled"""

		return frappe.get_list("Item", {"item_type": "SKU", "disabled": "0"},
			["name", "item_name", "able", "item_group"])


	def on_submit(self):
		"""Submit all the Detalle de Pedido that are linked with the doc"""

		filters = { "parent": self.name, "docstatus": ["!=", "2"] }

		for current in frappe.get_list("Detalle de Pedido", filters):
			doc = frappe.get_doc("Detalle de Pedido", current.name)
			doc.submit()
		create_material_request(self)


	def on_cancel(self):
		"""Cancel all the Detalle de Pedido that are linked with the doc"""

		filters = { "parent": self.name, "docstatus": ["!=", "2"] }

		for current in frappe.get_list("Detalle de Pedido", filters):
			doc = frappe.get_doc("Detalle de Pedido", current.name)
			doc.cancel()

	def on_trash(self):
		"""Delete all the Detalle de Pedido that are linked with the doc"""

		filters = { "parent": self.name }

		for current in frappe.get_list("Detalle de Pedido", filters):
			doc = frappe.get_doc("Detalle de Pedido", current.name)

			if doc.docstatus == 1.000:
				doc.cancel()

			doc.delete()

@frappe.whitelist()
def create_material_request(self):
		data = frappe.get_list("Detalle de Pedido", {"parent": ["=", self.name], "docstatus": ["!=", "2"]}, ["sku", "order_sku_total"])
		items = []
		for value in data:
			item = {'item_code': value.sku,
					'qty': value.order_sku_total,
					'schedule_date': self.fecha_de_entrega,
					'warehouse': self.deposito}
			items.append(item)
			
			
		material_request = frappe.get_doc({
			"doctype": "Material Request",
			"company": "Heladom",
			'naming_series': 'MREQ-',
			'material_request_type': 'Material Transfer',
			'source_warehouse': self.almacen,
			'target_warehouse': self.deposito,
			'items':items
		})
		material_request.insert()
		material_request.save()
