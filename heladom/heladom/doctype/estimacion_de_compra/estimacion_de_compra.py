# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class EstimaciondeCompra(Document):
	pass


@frappe.whitelist()
def get_estimation_info(start_date, end_date):
	start_date = start_date.replace(".", "")
	end_date = end_date.replace(".", "")
	sql = frappe.db.sql("""SELECT * FROM tabSKU""", as_dict=1)
	result = []
	for sku in sql:
		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (start_date, end_date ,sku.name,))
		avg = frappe.db.sql("""select @prom""")[0][0]
		sku.avg = avg
		result.append(sku)
	return result