# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

import frappe

def item_validate(doc, event):
	pass
	# validate_that_purchase_conversion_factor_is_set(doc)
	# validate_conversion_factors_table_against_generic(doc)

def validate_conversion_factors_table_against_generic(item_doc):
	# fetch from the database the configuration
	only_minimum_factors = frappe.db.get_single_value("Configuracion",
		"validate_conversion_factors_table_against_generic")

	if item_doc.item_type == "SKU":
		generic_doc = frappe.get_doc("Generico", item_doc.generic)

		for conversion_factor in item_doc.conversion_factors:
			if not conversion_factor.to_uom == generic_doc.uom and only_minimum_factors:
				frappe.throw("¡La unidad minima en la tabla Factores de Conversion debe \
					coincidir con la unidad minima en el Generico!")
				
def validate_that_purchase_conversion_factor_is_set(item_doc):
	if item_doc.item_type == "SKU":
		for conversion_factor in item_doc.conversion_factors:
			if conversion_factor.from_uom == item_doc.stock_uom:
				# then break it
				break
		else:
			frappe.throw("¡No se encontro el factor de conversion de la unidad de compra {0}\
				en la tabla Factores de Conversion!".format(item_doc.stock_uom))