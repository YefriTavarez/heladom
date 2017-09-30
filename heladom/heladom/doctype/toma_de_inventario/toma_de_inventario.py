# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
from collections import defaultdict

class TomadeInventario(Document):
	def on_submit(self):
		if self.tipo_toma == "Inventario Diario":
			inventario_diario(self.item_table)
		else:
			inventario_fisico(self.item_table, self.name)
			inventario_diario(self.item_table)

def inventario_fisico(item_table, name):
	items = group_items_sku(item_table)
	register(items, name)
	create_material_issue(items)

def inventario_diario(item_table):
	items = group_items_insumo(item_table)
	items_insumo = as_insumo(items)
	create_stock_reconciliaton(items_insumo)

def register(items, toma_nombre):
	for item in items:
		cantidad_actual = frappe.get_value('Stock Ledger Entry', filters={'item_code': item["item_code"], 'warehouse': item["warehouse"]}, fieldname=['qty_after_transaction'])
		record = frappe.get_doc({
			"doctype": "Retail Food Ledger",
			"company": "Heladom",
			"sku": item["item_code"],
			"generico": frappe.get_value('Item', filters={'item_code': item["item_code"]}, fieldname=['generic']),
			"clave_de_rotacion": frappe.get_value('Item', filters={'item_code': item["item_code"]}, fieldname=['rotation_key']),
			"insumo": frappe.get_value('Item', filters={'item_code': item["item_code"]}, fieldname=['insumo']),
			"centro_de_costo": item["warehouse"],
			"fecha_transacion": datetime.now().date(),
			"tipo_referencia": "Toma de Inventario",
			"nombre_referencia": toma_nombre,
			"unidad_minima": frappe.get_value('Item', filters={'item_code': item["item_code"]}, fieldname=['stock_uom']),
			"existencia": item["qty"],
			"consumo": cantidad_actual - item["qty"]
		})
		record.insert()
		record.save()

def create_material_issue(items):
	item_table = []
	for item in items:
		cantidad_actual = frappe.get_value('Stock Ledger Entry', filters={'item_code': item["item_code"], 'warehouse': item["warehouse"]}, fieldname=['qty_after_transaction'])
		item_table.append({
			"item_code": item["item_code"],
			"s_warehouse": item["warehouse"],
			"qty": cantidad_actual - item["qty"],
			"uom": frappe.get_value('Item', filters={'item_code': item["item_code"]}, fieldname=['stock_uom']),
			"conversion_factor": 1,
			"stock_uom": frappe.get_value('Item', filters={'item_code': item["item_code"]}, fieldname=['stock_uom']),
			"transfer_qty": cantidad_actual - item["qty"]
		})
	material_issue = frappe.get_doc({
		"doctype": "Stock Entry",
		"naming_series": "STE-",
		"purpose": "Material Issue",
		"company": "Heladom",
		"from_warehouse": items[0]["warehouse"],
		"items": item_table
	})
	material_issue.insert()
	material_issue.save()
	material_issue.submit()

def create_stock_reconciliaton(items):
	stock_reconciliation = frappe.get_doc({
		"doctype": "Stock Reconciliation",
		"naming_series": "SR/",
		"company": "Heladom",
		"posting_date": datetime.now().date(),
		"posting_time": datetime.now().time(),
		"expense_account": "Ajuste de existencias - H",
		"cost_center": "Principal - H",
		"items": items
	})
	stock_reconciliation.insert()
	stock_reconciliation.save()
	stock_reconciliation.submit()

def group_items_insumo(item_table):
	groups = defaultdict(list)
	item_list = []

	for item in item_table:
	    groups[item.item].append(item)

	for item in groups.values():
		cantidad = 0
		valuation_rate = 0
		for i in item:
			cantidad += float(i.cantidad) * float(i.conversion)
		valuation_rate=frappe.get_all('Stock Ledger Entry', filters={'item_code': item[0].item, 'warehouse': item[0].almacen},fields=['valuation_rate'])

		try:
		    valuation_rate = valuation_rate[0].valuation_rate
		except IndexError:
		    frappe.errprint("El Item no tiene Valor de Costo")

		item_dic = {
			"item_code": item[0].item,
			"warehouse": item[0].almacen,
			"qty": cantidad,
			"valuation_rate": valuation_rate
		}
		item_list.append(item_dic)

	return item_list

def group_items_sku(item_table):
	groups = defaultdict(list)
	item_list = []

	for item in item_table:
	    groups[item.item].append(item)

	for item in groups.values():
		cantidad = 0
		for i in item:
			cantidad += float(i.cantidad) * float(i.conversion)

		item_dic = {
			"item_code": item[0].item,
			"warehouse": item[0].almacen,
			"qty": cantidad
		}
		item_list.append(item_dic)

	return item_list

def as_insumo(item_list_sku):
	item_insumo_list = []
	groups = defaultdict(list)
	items_insumo = []
	for item_sku in item_list_sku:
		item_insumo_dic = {
			"item_code": item_sku["item_code"],
			"warehouse": item_sku["warehouse"],
			"qty": item_sku["qty"],
			"valuation_rate": item_sku["valuation_rate"],
			"insumo": frappe.get_value('Item', item_sku["item_code"], 'insumo'),
			"conversion": frappe.get_value('Item', item_sku["item_code"], 'conversion_ins')
		}
		item_insumo_list.append(item_insumo_dic)

	for item_insumo in item_insumo_list:
	    groups[item_insumo["insumo"]].append(item_insumo)

	for item in groups.values():
		warehouse = frappe.get_value("Warehouse", item[0]["warehouse"], "almacen_ins")
		cantidad = 0
		valuation_rate = 0
		d = 0
		for i in item:
			cantidad += float(i["qty"]) * float(i["conversion"])
			valuation_rate += float(i["valuation_rate"])/float(i["conversion"])
			d += 1
		item_dic = {
			"item_code": item[0]["insumo"],
			"warehouse": warehouse,
			"qty": cantidad,
			"valuation_rate": valuation_rate/d
		}
		items_insumo.append(item_dic)

	return items_insumo
