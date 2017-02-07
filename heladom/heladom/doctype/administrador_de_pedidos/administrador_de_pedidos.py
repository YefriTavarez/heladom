# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class AdministradordePedidos(Document):
	def after_submit(self):
		# Crear una entrada en consumo de inventario
		pass