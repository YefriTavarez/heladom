# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe.utils import flt

developer_mode = frappe.db.get_single_value("Configuracion", "__developer_mode")

class InventarioFisicoHeladosItems(Document):
	def check_for_empty(self):
		failed = not self.tubo_qty and not self.pul_qty and not self.onces_qty

		if failed:
			frappe.throw("Es necesario que especifique la cantidad en por lo menos una de las\
				<br>tres unidades [Tubo | Pulgada | Onzas]", title="Fila No. {0}".format(self.idx))

		self.set_missing_values()

		# more_than_one = self.tubo_qty ^ self.pul_qty ^ self.onces_qty

	def set_missing_values(self):
		cut_off_date = self.get_last_cut_off_date()

		last_qty = self.get_last_qty(cut_off_date)
		stock_in = self.get_stock_in(cut_off_date)

		# do not calculate if we are in developer mode
		if not developer_mode:
			self.consumo = flt(last_qty) + flt(stock_in) - flt(self.onces_total)

	def get_last_qty(self, cut_off_date):
		return frappe.get_value("Retail Food Ledger", {
			"sku": self.sku,
			"fecha_transacion": ["=", cut_off_date],
		}, ["existencia"])

	def get_stock_in(self, cut_off_date):
		stock_in = 0.000

		stock_in_list = frappe.get_list("Retail Food Ledger", {
			"sku": self.sku,
			"fecha_transacion": [">=", cut_off_date],
			"fecha_transacion": ["<", self.date],
			"entrada": [">", 0.000]
		}, ["entrada"])

		for stock in stock_in_list:
			stock_in += flt(stock_in)

		return stock_in
	
	def get_last_cut_off_date(self):
		self.date = frappe.get_value("Inventario Fisico Helados", 
			self.parent, "date")

		period_length = frappe.db.get_single_value("Configuracion", 
			"period_length")

		return frappe.utils.add_days(self.date, - int(period_length))


def as_datetime(string_date):
	from datetime import datetime

	date = string_date

	if isinstance(string_date, basestring):
		date = datetime.strptime(cut_off_date, frappe.utils.DATE_FORMAT)

	return date




