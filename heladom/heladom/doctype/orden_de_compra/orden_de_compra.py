# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json

class OrdendeCompra(Document):
	def on_submit(self):							
		esc = frappe.get_doc("Estimacion de Compra", self.created_from)
		esc.order_sku_real_reqd = self.order_sku_real_reqd
		esc.logistica = self.logistica
		esc.mercadeo = self.mercadeo
		esc.planta = self.planta
		esc.order_sku_total = self.order_sku_total

		esc.db_update()

@frappe.whitelist()
def get_estimation_skus(estimation):
	sql = frappe.db.sql("""SELECT sku, sku_name, general_coverage, reqd_option_1, reqd_option_2, reqd_option_3,
								required_qty, order_sku_existency, order_sku_in_transit, order_sku_real_reqd,
								logistica, mercadeo, planta, order_sku_total
							FROM `tabEstimacion SKUs`
							WHERE parent = '%s' """ % (estimation,), as_dict=1)

	return sql

@frappe.whitelist()
def add_new_orden_de_compra(estimation, estimation_date, estimation_supplier):
	message = 'error'
	estimation_skus = frappe.db.sql("""SELECT sku, sku_name, general_coverage, reqd_option_1, reqd_option_2, reqd_option_3,
								required_qty, order_sku_existency, order_sku_in_transit, order_sku_real_reqd,
								logistica, mercadeo, planta, order_sku_total
							FROM `tabEstimacion SKUs`
							WHERE parent = '%s' """ % (estimation,), as_dict=1)

	# skus = []
	# for sku in estimation_skus:
	#     skus.append({
	#         "sku": sku.sku,
	#         "sku_name": sku.sku_name,
	#         "general_coverage": sku.general_coverage,
	#         "reqd_option_1": sku.reqd_option_1,
	#         "reqd_option_2": sku.reqd_option_2,
	#         "reqd_option_3": sku.reqd_option_3,
	#         "required_qty": sku.required_qty,
	#         "order_sku_existency": sku.order_sku_existency,
	#         "order_sku_in_transit": sku.order_sku_in_transit,
	#         "order_sku_real_reqd": sku.order_sku_real_reqd,
	#         "logistica": sku.logistica,
	#         "mercadeo": sku.mercadeo,
	#         "planta": sku.planta,
	#         "order_sku_total": sku.order_sku_total,
	#         "estimation_reference": estimation
	#         })
	try:
		order = frappe.get_doc({
			"doctype": "Orden de Compra"
		})
		order.insert()

		# order.append("estimations", {
		#             "estimation": estimation
		#         })

		# for sku in estimation_skus:
		#     order.append("estimations_skus", {
		#         "sku": sku.sku,
		#         "sku_name": sku.sku_name,
		#         "general_coverage": sku.general_coverage,
		#         "reqd_option_1": sku.reqd_option_1,
		#         "reqd_option_2": sku.reqd_option_2,
		#         "reqd_option_3": sku.reqd_option_3,
		#         "required_qty": sku.required_qty,
		#         "order_sku_existency": sku.order_sku_existency,
		#         "order_sku_in_transit": sku.order_sku_in_transit,
		#         "order_sku_real_reqd": sku.order_sku_real_reqd,
		#         "logistica": sku.logistica,
		#         "mercadeo": sku.mercadeo,
		#         "planta": sku.planta,
		#         "order_sku_total": sku.order_sku_total,
		#         "estimation_reference": estimation
		#         })

		order.insert()
		message = 'success'
	except Exception as e:
		raise
	
	return message