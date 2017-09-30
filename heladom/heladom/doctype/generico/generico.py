# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Generico(Document):
	
	def validate(self):
		if not self.is_new():
			self.update_items()

	def update_items(self):
		for item in self.get_items():

			# update the attributes in the items
			item.item_group = self.item_group

			# finally update the database
			item.db_update()

	def get_items(self):
		item_list = frappe.get_list("Item",
			{"generic": self.name})

		return [frappe.get_doc("Item", item.name)
			for item in item_list]
