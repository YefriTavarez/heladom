# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
import datetime

class EstimaciondeCompra(Document):
	def before_submit(self):
		# Crear una entrada en administrador de pedidos
		if self.is_warehouse_transfer:
			pedido = frappe.get_doc({
					"doctype": "Administrador de Pedidos",
					"date": self.date,
					"estimation": self.name,
					"cost_center": self.cost_center
					})

			for sku in self.estimation_skus:
				pedido.append("skus", {
					"doctype": "Pedido Skus",
					"sku": sku.sku,
					"sku_name": sku.sku_name,
					"qty": sku.order_sku_total
				})

			pedido.insert()


def validate_fields(obj):
	if not "cost_center" in obj or obj["cost_center"] == "":
		frappe.throw("Falta <b>Centro de costo!</b>")

	if not "supplier" in obj:
		frappe.throw("Falta <b>Suplidor!</b>")

	if not "estimation_type" in obj or obj["estimation_type"] == "":
		frappe.throw("Falta <b>Tipo de Estimacion!</b>")

	if not "cut_trend" in obj:
		frappe.throw("Falta <b>Corte de Tendencia!</b>")

	if not "presup_gral" in obj:
		frappe.throw("Falta <b>Presupuesto General!</b>")
		
	if not "date_cut_trend" in obj:
		frappe.throw("Falta <b>Fecha Inicio</b>!")

	if not "cut_trend_week" in obj:
		frappe.throw("Falta <b>Fecha Final</b>!")

	if not "transit" in obj:
		frappe.throw("Falta Cantidad de semanas en <b>Transito</b>!")

	if not "consumption" in obj:
		frappe.throw("Falta Cantidad de semanas de <b>Consumo</b>!")

	if not "coverage" in obj:
		frappe.throw("Falta Cantidad de semanas de <b>Cobertura!</b>")

	if not "date" in obj:
		frappe.throw("Falta <b>Fecha!</b>")


