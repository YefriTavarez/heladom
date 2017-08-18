# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe

__version__ = '2.0.0'

# doc is type of Inventario Fisico Helados
def ledger_entry_from_inventario(doc):
	"""Method to create all the required Mayor de Helados from an Inventario Fisico Helados"""

	for item in doc.items:
		ledger = frappe.new_doc("Retail Food Ledger")

		ledger.company = doc.company
		ledger.sku =  item.sku
		ledger.generico = item.sku_generic
		ledger.insumo = item.sku_insumo
		ledger.clave_de_rotacion = item.clave_de_rotacion
		ledger.centro_de_costo = doc.cost_center
		ledger.fecha_transacion = doc.date
		ledger.tipo_referencia = item.doctype
		ledger.nombre_referencia = item.name
		ledger.voucher_type = doc.doctype
		ledger.voucher_name = doc.name
		ledger.unidad_minima = frappe.get_value("Generico", item.sku_generic, "uom")
		ledger.existencia = item.onces_total
		ledger.consumo = item.consumo
		
		ledger.flags.ignore_permissions = True
		ledger.insert()

def delete_ledger_entry_from_inventario(doc):
	"""Method to delete all the related Mayor de Helados to this Inventario Fisico Helados"""

	for item in doc.items:
		ledger = frappe.get_doc("Retail Food Ledger", { 
			"nombre_referencia": item.name })

		if ledger.docstatus == 1:
			ledger.cancel()

		ledger.delete()

@frappe.whitelist()
def update_item_group(is_sku, sku, generico):
	if is_sku:
		item_doc = frappe.get_doc("Item", sku)
		uom = frappe.get_value("Generico", generico, "uom")

		item_doc.stock_uom = uom
		item_doc.db_update()





