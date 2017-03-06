# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class GeneradordeEstimaciones(Document):
	def crear_estimaciones(self):
		# Constants with default values
		CUT_TREND_DEFAULT = 10
		PRESUP_GRAL_DEFAULT = 25
		TRANSIT_WEEKS_DEFAULT = 8
		CONSUMPTION_WEEKS_DEFAULT = 9
		COVERAGE_WEEKS_DEFAULT = 17

		listado_estimaciones = []
		listado_skus = self.listado_sku_habiles_para_estimacion()

		if self.active_skus:
			listado_skus = self.listado_sku_activos()

		for sku in listado_skus:
			if self.rotation_key and not self.rotation_key == sku.rotation_key:
				continue

			if self.stimation_type:
				item_group = frappe.db.get_value("Item", sku.item, "item_group")

				if not item_group == self.stimation_type:
					continue

			if self.sku_able and not sku.able_to_estamation:
				continue

			estimacion_de_compra = frappe.get_doc({
				"doctype" : "Estimacion de Compra", 
				"date" : self.date,
				"supplier" : "Baskin Robbins internacional",
				"cut_trend" : CUT_TREND_DEFAULT,
				"presup_gral" : PRESUP_GRAL_DEFAULT,
				"transit_weeks" : TRANSIT_WEEKS_DEFAULT,
				"consumption_weeks" : CONSUMPTION_WEEKS_DEFAULT,
				"coverage_weeks" : COVERAGE_WEEKS_DEFAULT,
				"current_date" : self.year_week,
				"sku" : sku.name
			})

			estimacion_de_compra.save()

			listado_estimaciones.append(estimacion_de_compra.name)

		return listado_estimaciones

	def listado_sku_habiles_para_estimacion(self):
		return frappe.get_list("SKU", fields=["name", "rotation_key", "item", "able_to_estamation"])

	def listado_sku_activos(self):
		return frappe.db.sql("""SELECT DISTINCT child.name, child.rotation_key, child.item, child.able_to_estamation
			FROM tabSKU AS child
			JOIN `tabEstimacion de Compra` AS parent 
			ON child.name = parent.sku 
			WHERE parent.date BETWEEN '%(start_date)s' AND '%(end_date)s'""" 
			% { "start_date" : self.start_date, "end_date": self.end_date },
			as_dict=True)