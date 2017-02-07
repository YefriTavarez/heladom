# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Liquidacion(Document):
	pass

@frappe.whitelist()
def get_international_order_info(international_order):
	result = frappe.db.sql("""SELECT ocp.sku, ocp.sku_name, ocp.order_sku_total, s.arancel
								FROM `tabFactura Internacional` as fi
								JOIN `tabOrden de Compra` as oc ON oc.name = fi.order
								JOIN `tabOrden de Compra Productos` as ocp ON ocp.parent = oc.name
								JOIN  `tabSKU` as s ON s.name = ocp.sku
								WHERE fi.name = '%s'""" % (international_order,), as_dict=1)
	return result