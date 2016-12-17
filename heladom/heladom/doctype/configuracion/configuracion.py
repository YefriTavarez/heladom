# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Configuracion(Document):
	pass

@frappe.whitelist()
def get_configuration_info():
	sql = frappe.db.sql("""SELECT field, value 
							FROM tabSingles 
							WHERE doctype = 'Configuracion'
								AND field = 'weeks' OR field = 'general_percent'""", as_dict=1)

	info = {
		sql[0].field: sql[0].value,
		sql[1].field: sql[1].value,
	}
	return info