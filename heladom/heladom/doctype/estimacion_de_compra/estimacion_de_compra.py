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


@frappe.whitelist()
def get_estimation_info(doc):
	doc = json.loads(doc)
	now = datetime.datetime.now()
	current_year = now.year
	last_year = current_year - 1

	validate_fields(doc)

	end_date = doc["cut_trend_week"]
	start_date = doc["date_cut_trend"]
	supplier = doc["supplier"]
	cost_center = doc["cost_center"]
	cut_trend = doc["cut_trend"]	
	estimation_type = doc["estimation_type"]
	presup_gral = doc["presup_gral"]
	transit_weeks = doc["transit"]
	consumption_weeks = doc["consumption"]
	

	last_year_start_week = int(end_date.split(".")[1]) + 1
	last_year_transit_end_week = last_year_start_week + transit_weeks - 1
	last_year_transit_start_date = str(last_year) + str(last_year_start_week) 
	last_year_transit_end_date = str(last_year) + str(last_year_transit_end_week)

	last_year_consumption_start_week = last_year_transit_end_week + 1
	last_year_consumption_end_week = last_year_consumption_start_week + consumption_weeks - 1

	last_year_consumption_start_date = str(last_year) + str(last_year_consumption_start_week)

	if last_year_consumption_end_week > 52:
		last_year_consumption_end_date = str(current_year) + str(last_year_consumption_end_week - 52)
	else:
		last_year_consumption_end_date = str(last_year) + str(last_year_consumption_end_week)


	start_date = start_date.replace(".", "")
	end_date = end_date.replace(".", "")

	current_start_date = start_date.replace(str(last_year), str(current_year))
	current_end_date = end_date.replace(str(last_year), str(current_year))

	sql = frappe.db.sql("""SELECT * FROM tabSKU""", as_dict=1)

	result = []
	for sku in sql:
		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (start_date, end_date ,sku.name,))
		last_avg = frappe.db.sql("""select @prom""")[0][0]
		sku.last_year_avg = last_avg

		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (current_start_date, current_end_date ,sku.name,))
		current_avg = frappe.db.sql("""select @prom""")[0][0]
		sku.current_year_avg = current_avg

		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (current_start_date, current_end_date ,sku.name,))
		current_avg = frappe.db.sql("""select @prom""")[0][0]
		sku.current_year_avg = current_avg

		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (last_year_transit_start_date, last_year_transit_end_date ,sku.name,))
		last_year_transit_avg = frappe.db.sql("""select @prom""")[0][0]
		sku.last_year_transit_avg = last_year_transit_avg

		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (last_year_consumption_start_date, last_year_consumption_end_date ,sku.name,))
		last_year_consumption_avg = frappe.db.sql("""select @prom""")[0][0]
		sku.last_year_consumption_avg = last_year_consumption_avg

		result.append(sku)
	return result

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
