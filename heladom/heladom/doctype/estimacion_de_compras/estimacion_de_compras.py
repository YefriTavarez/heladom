# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt

class EstimaciondeCompras(Document):
	
	def crear_estimaciones(self):
		"""Create a new set of Detalle de Estimacion based on the current Estimacion de Compras filters"""
		
		for generico in self.get_genericos():
			if not generico.item_group == self.estimation_type:
				continue

			if self.sku_able and not generico.enabled:
				continue

			detalle = self.crear_estimacion(generico.name)

			if detalle.sku:
				detalle.insert()

	def crear_estimacion(self, generico):
		"""Create a new Detalle de Estimacion based on the current Estimacion de Compras"""
		
		# allocate a new doc in memory
		detalle = frappe.new_doc("Detalle de Estimacion")

		if self.is_new():
			frappe.throw(msg="¡Estimacion de Compra no encontrada!", title="¡Atencion requerida!")

		# copying the header
		detalle.date = self.date
		detalle.cost_center = self.cost_center
		detalle.supplier = self.supplier
		detalle.cut_trend = self.cut_trend
		detalle.presup_gral = self.presup_gral
		detalle.transit_weeks = self.transit_weeks
		detalle.arrival_date = self.arrival_date
		detalle.consumption_date = self.consumption_date
		detalle.coverage_date = self.coverage_date
		detalle.parent = self.name
		detalle.generico = generico
		# detalle.sku = sku

		detalle.set_missing_values()

		if detalle.sku:
			item_dict = frappe.get_value("Item", {
				"name": detalle.sku
			}, ["relative_coverage", "rotation_key"], as_dict=True)

			detalle.cobertura_relativa = item_dict.get("relative_coverage")
			detalle.consumption_weeks = flt(self.consumption_weeks) + flt(item_dict.get("relative_coverage"))
			detalle.coverage_weeks = flt(self.coverage_weeks) + flt(item_dict.get("relative_coverage"))
			detalle.rotation_key = item_dict.get("rotation_key")

		return detalle


	def get_genericos(self):
		"""Fetch from the Database all the SKU Items that are not disabled"""
		
		doctype = "Generico"
		filters = {"enabled": "1"}
		fields = ["name", "code", "generic_name", "enabled", "item_group"]

		# query and return the results
		return frappe.get_all(doctype, fields, filters)

	
	def on_submit(self):
		"""Submit all the Detalle de Estimacion that are linked with the doc"""

		filters = { "parent": self.name, "docstatus": ["!=", "2"] }

		for current in frappe.get_all("Detalle de Estimacion", filters):
			doc = frappe.get_doc("Detalle de Estimacion", current.name)
			doc.submit()

	def on_cancel(self):
		"""Cancel all the Detalle de Estimacion that are linked with the doc"""
		
		filters = { "parent": self.name, "docstatus": ["!=", "2"] }

		for current in frappe.get_all("Detalle de Estimacion", filters):
			doc = frappe.get_doc("Detalle de Estimacion", current.name)
			doc.cancel()

	def on_trash(self):
		"""Delete all the Detalle de Estimacion that are linked with the doc"""
		
		filters = { "parent": self.name }

		for current in frappe.get_all("Detalle de Estimacion", filters):
			doc = frappe.get_doc("Detalle de Estimacion", current.name)

			if doc.docstatus == 1.000:
				doc.cancel()

			doc.delete()
