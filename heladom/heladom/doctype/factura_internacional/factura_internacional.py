# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FacturaInternacional(Document):
	def on_submit(self):
		for sku in self.skus:
			frappe.db.sql("""UPDATE `tabOrden de Compra Productos`
							SET order_sku_total = %d
							WHERE parent = '%s' AND sku = '%s'
							""" % (sku.qty, self.order, sku.sku))

			frappe.db.sql("""UPDATE `tabEstimacion SKUs`
							SET order_sku_total = %d
							WHERE parent = '%s' AND sku = '%s'
							""" % (sku.qty ,sku.estimation_reference, sku.sku))

		estimations = frappe.db.sql("""SELECT estimation 
										FROM `tabEstimaciones Orden de Compra`
										WHERE parent = '%s'""" % (self.order,), as_dict=1)

		for estimation in estimations:
			frappe.db.sql("""UPDATE `tabEstimacion de Compra`
								SET was_received = 1
								WHERE name = '%s' """ % (estimation.estimation,))


@frappe.whitelist()
def get_order_skus(order):
	result = frappe.db.sql("""SELECT sku, sku_name, order_sku_total, estimation_reference
								FROM `tabOrden de Compra Productos`
								WHERE parent = '%s'
							""" % (order,), as_dict=1)

	return result