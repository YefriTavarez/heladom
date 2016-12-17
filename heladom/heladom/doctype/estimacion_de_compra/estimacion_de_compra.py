# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class EstimaciondeCompra(Document):
	pass


@frappe.whitelist()
def get_estimation_info(doctype):
	sql = frappe.db.sql("""SELECT * FROM tabSKU""", as_dict=1)
	return sql