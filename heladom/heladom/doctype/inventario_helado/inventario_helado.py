# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class InventarioHelado(Document):
	pass

@frappe.whitelist()
def get_sku_info(sku):
	sql = frappe.db.sql("""SELECT s.*, g.generic_name
							FROM tabSKU as s
							JOIN tabGenericos as g ON g.name = s.generic
							WHERE s.name = '%s'""" % (sku,), as_dict=1)
	message = "error"
	if len(sql) == 0:
		return message
	else:
		return sql[0]