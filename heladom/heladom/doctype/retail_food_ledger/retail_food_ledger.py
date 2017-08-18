# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RetailFoodLedger(Document):
	def validate(self):
		self.validate_stock_and_in()

	def validate_stock_and_in(self):

		if self.entrada and self.existencia:
			frappe.throw("¡Inserte un registro para las entradas \
				y luego otro registro para las existencias!")
