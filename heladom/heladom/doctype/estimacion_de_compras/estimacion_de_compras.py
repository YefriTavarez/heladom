# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

CUTOFF_TREND_DEFAULT = frappe.db.get_single_value("Configuracion", "weeks")
PRESUP_GRAL_DEFAULT = frappe.db.get_single_value("Configuracion", "general_percent")

class EstimaciondeCompras(Document):
	def validate(self):
		self.linked_docs = []
		for child in self.items:
			self.linked_docs.append(child.codigo)

		self.set_header_info()
		self.update_detalles()

	def update_detalles(self):
		for d in frappe.get_list("Detalle de Estimacion", fields=["name", "parent"]):
			if d.parent == self.name and not d.name in self.linked_docs:
				doc = frappe.get_doc("Detalle de Estimacion", d.name)
				self.append("items", {
					"cierre": doc.date,
					"codigo": doc.name,
					"promedio": doc.current_year_avg,
					"detalle_estimacion": doc.name,
					"prevision": doc.required_qty,
					"duracion": doc.coverage_weeks,
					"descripcion": "{0} {1}".format(doc.sku, doc.sku_name)
				})

	def remove_complement(self):
		deleted_list = []
		self.linked_docs = []
		for child in self.items:
			self.linked_docs.append(child.codigo)

		for d in frappe.get_list("Detalle de Estimacion", fields=["name", "parent"]):
			if d.parent == self.name and not d.name in self.linked_docs:
				childname = frappe.get_value("Estimacion de Compra Hijo", {"codigo": d.name}, "name")
				child = frappe.get_doc("Estimacion de Compra Hijo", childname)
				if child.docstatus == 0:
					child.codigo = None
					child.save()
					child.delete()

				self.db_update()
				
				doc = frappe.get_doc("Detalle de Estimacion", d.name)
				deleted_list.append(d.name)
				doc.delete()

		return deleted_list

	def set_header_info(self):
		for docname in self.linked_docs:
			doc = frappe.get_doc("Detalle de Estimacion", docname)
			doc.supplier = self.supplier
			doc.date = self.date
			doc.cost_center = self.cost_center
			doc.estimation_type = self.estimation_type
			doc.presup_gral = self.presup_gral
			doc.cut_trend = self.cut_trend
			doc.transit_weeks = self.transit_weeks
			doc.arrival_date = self.arrival_date
			doc.consumption_weeks = self.consumption_weeks
			doc.consumption_date = self.consumption_date
			doc.coverage_weeks = self.coverage_weeks
			doc.coverage_date = self.coverage_date

			doc.save()

	def on_submit(self):
		for docname in self.linked_docs:
			doc = frappe.get_doc("Detalle de Estimacion", docname)
			doc.submit()

	def on_cancel(self):
		for child in self.items:
			doc = frappe.get_doc("Detalle de Estimacion", child.codigo)
			doc.cancel()


	def crear_estimacion(self):
		if not hasattr(self, "sku"):
			frappe.throw("Missing SKU")

		if self.is_new():
			frappe.throw(msg="<b>Estimacion de Compra</b> no encontrada!", title="Atencion")

		detalle_estimacion = frappe.get_doc({
			"doctype" : "Detalle de Estimacion", 
			"date" : self.date,
			"cost_center" : self.cost_center,
			"supplier" : self.supplier,
			"cut_trend" : CUTOFF_TREND_DEFAULT,
			"presup_gral" : PRESUP_GRAL_DEFAULT,
			"transit_weeks" : self.transit_weeks,
			"consumption_weeks" : self.consumption_weeks,
			"coverage_weeks" : self.coverage_weeks,
			"parent" : self.name,
			"sku" : self.sku,
			"needs_to_save" : 1
		})

		detalle_estimacion.set_missing_values()
		detalle_estimacion.save()

		return detalle_estimacion

	def crear_estimaciones(self):
		for sku in self.listado_skus():
			if self.rotation_key and not self.rotation_key == sku.rotation_key:
				continue

			if not sku.item_group == self.estimation_type:
				continue

			if self.sku_able and not sku.able:
				continue

			# set global to access it from crear_estimacion
			self.sku = sku.name
			detalle_estimacion = self.crear_estimacion()

		self.save()

	def listado_skus(self):
		
		# let's set the filters
		filters = {"is_sku": 1}
		
		# now we're listing the fileds that we want
		field_list = ["name", "rotation_key", "item_name", "able", "item_group"]

		# query and return the results
		return frappe.get_list("Item", field_list, filters)

	def on_trash(self):

		# empty the list
		self.linked_docs = []

		for child in self.items:
			self.linked_docs.append(child.codigo)
			
			if child.docstatus == 0:
				child.codigo = None
				child.save()
		
		for docname in self.linked_docs:
			try:
				doc = frappe.get_doc("Detalle de Estimacion", docname)
				doc.delete()
			except:
				pass # any errors in here? let's just ignore them
