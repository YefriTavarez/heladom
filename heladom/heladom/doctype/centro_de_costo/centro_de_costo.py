# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Centrodecosto(Document):
	pass


@frappe.whitelist()
def get_cost_center_info(cost_center_admin):
	sql = frappe.db.sql("""SELECT * FROM `tabCentro de costo`
		WHERE center_admin = '%s'""" 
		% (cost_center_admin), as_dict=1)

	if sql:
		return sql[0]

	return frappe.get_doc({"doctype": "Centro de costo"})
	