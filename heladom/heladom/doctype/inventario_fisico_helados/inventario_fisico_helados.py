# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from heladom.constants import WEEK_DAY_SET
from heladom.api import validate_current_date as check_date
from heladom import ledger_entry_from_inventario as create_ledger
from heladom import delete_ledger_entry_from_inventario as delete_ledger

day = frappe.db.get_single_value("Configuracion", "default_week_day", cache=False)
week_day = [e.get("label") for e in WEEK_DAY_SET if e.get("value") == str(day)][0]

class InventarioFisicoHelados(Document):

	def autoname(self):
		# from frappe.model.naming import make_autoname
		abbr = frappe.get_value("Company", self.company, "abbr")

		d = str(self.date).replace("-", "")
		self.name = "{0}{1} - {2}".format(
			self.cost_center, d, abbr)

	def validate(self):
		check_date(self.date, day, week_day)

		self.validate_children()

	def validate_children(self):
		for item in self.items:
			item.check_for_empty()

	def on_submit(self):
		create_ledger(self)

	def on_cancel(self):
		delete_ledger(self)
