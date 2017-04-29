# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from constants import ZERO, DRAFT, SUBMITTED, CANCELLED, MONDAY, WEEK_DAYS, WEEKS_IN_YEAR

def get_final_order_stock(date, sku):	
	stock = frappe.db.sql("""
		SELECT SUM(child.onces_total)
		FROM `tabInventario Fisico Helados Items` AS child 
		JOIN `tabInventario Fisico Helados` AS parent 
		ON child.parent = parent.name 
		WHERE child.sku = '%(sku)s' 
		AND parent.date = '%(date)s'"""
	% { "sku" : sku, "date" : date })

	if stock[ZERO][ZERO]:
		return float(stock[ZERO][ZERO])

	return float(ZERO)

def get_total_in_transit(sku):	
	total = frappe.db.sql("""
		SELECT SUM(order_sku_total)
		FROM `tabDetalle de Estimacion`		
		WHERE sku = '%(sku)s' 
		AND was_received <> 1
		AND docstatus = %(submitted)s"""
	% { "sku" : sku, "submitted": SUBMITTED})

	if total[ZERO][ZERO]:
		return float(total[ZERO][ZERO])

	return float(ZERO)


def get_average(start_date, end_date, sku):
	frappe.db.sql(
		"""CALL GetPromedioHistorico('%(from_date)s', '%(to_date)s', '%(sku)s', @average)""" 
			% { "from_date" : start_date, "to_date" : end_date, "sku" : sku })

	average = frappe.db.sql("""SELECT @average""")[ZERO][ZERO]

	if not average:
		return float(0)

	return round(average, 2)

def get_sku_list(supplier, sku_group=None):
	def get_filters(sku_group):
		if sku_group:
			return "AND item.item_group = '{0}'".format(sku_group)

		return ""

	return frappe.db.sql("""
		SELECT sku.name sku, sku.item sku_name, sku.able_to_estamation, sku.available_locally, sku.pieces_per_level, 
			sku.rotation_key, sku.code, sku.pieces_per_pallet, sku.arancel, sku.generic
		FROM tabSKU AS sku 
		JOIN tabItem AS item 
		ON sku.item = item.name 
		WHERE item.default_supplier = '%(default_supplier)s'
		AND sku.able_to_estamation = 1 %(filter)s"""
	% { "default_supplier": supplier, "filter": get_filters(sku_group) }, as_dict=True)

def validate_current_date(date):
	from datetime import datetime
	dateobj = date if not isinstance(date, unicode) else datetime.strptime(date,"%Y-%m-%d")
	if not dateobj.isoweekday() == MONDAY:
		frappe.throw(msg="Valor del campo <i>Fecha</i> debe corresponder a un lunes de la semana",title="Error de Fecha")


def add_days(date, days):
	return add_to_date(date, days=days)

def add_weeks(date, weeks):
	days = weeks * WEEK_DAYS
	return add_days(date, days)

def add_years(date, years):
	weeks = years * WEEKS_IN_YEAR
	return add_weeks(date, weeks)

def add_to_date(date, years=0, months=0, days=0):
	return frappe.utils.add_to_date(date, years, months, days)

def fetch_as_array(date, weeks):
	monday_dates = []

	monday_dates.append(date)

	for week in xrange(1, weeks):
		next_week = week * WEEK_DAYS
		monday_dates.append(add_days(date, next_week))

	return monday_dates


@frappe.whitelist()
def crear_orden_de_compra(estimacion):
	esc = frappe.get_doc("Estimacion de Compra", estimacion)
	esc.name = None
	esc.doctype = "Orden de Compra"

	import json
	json_str = frappe.as_json(esc)
	dictionary = json.loads(json_str)

	odc = frappe.get_doc(dictionary)
	odc.docstatus = DRAFT
	odc.created_from = estimacion
	odc.insert()

	return odc.name

@frappe.whitelist()
def existe_orden_de_compra(estimacion):
	order_list = frappe.get_list("Orden de Compra",
		filters={
			"created_from": estimacion,
			"docstatus": ("!=",CANCELLED)
		}
	)

	if order_list:
		odc = first(order_list)

		return odc.name

def first(array):
	if not array:
		array.append(float(ZERO))

	return array[ZERO]
