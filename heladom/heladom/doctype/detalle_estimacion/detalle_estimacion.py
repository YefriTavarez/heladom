# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json

class DetalleEstimacion(Document):
	def fill_tables(self):
		#for table in self.get_tablas_nombre():
		estimacion_de_compra = frappe.get_doc("Estimacion de Compra", self.get_stimation_name())
		estimacion_de_compra.fill_tables(self.codigo_sku)

		for history in reversed(estimacion_de_compra.recent_history):
			self.append("recent_history", history)

		for transit in estimacion_de_compra.transit_period:
			self.append("transit_period", transit)

		for transit in estimacion_de_compra.usage_period:
			self.append("usage_period", transit)



	def get_stimation_name(self):
		stimation_name = frappe.db.sql("""SELECT parent.name
			FROM `tabEstimacion de Compra` AS parent 
			JOIN `tabEstimacion SKUs` AS child 
			ON parent.name = child.parent 
			WHERE child.name = '%(estimacion_sku)s'""" 
		% { "estimacion_sku": self.sku})

		if not stimation_name[0][0]:
			frappe.throw("¡SKU no encontrado!")

		return stimation_name[0][0]