# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from constants import ZERO, DRAFT, SUBMITTED, CANCELLED, MONDAY, WEEK_DAYS, WEEKS_IN_YEAR

def get_final_order_stock(date, sku):	
	stock = frappe.db.sql("""SELECT SUM(child.onces_total)
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
	total = frappe.db.sql("""SELECT SUM(order_sku_total)
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

	# set the filters if the sku_group is set
	filters = { "item_group": sku_group } if sku_group else { }

	# return the results
	return frappe.get_list(doctype="Item", fields="*", filters=filters)

def validate_current_date(date):
	from datetime.datetime import strptime

	dateobj = strptime(date,"%Y-%m-%d") if isinstance(date, basestring) else date
	if not dateobj.isoweekday() == MONDAY:
		frappe.throw(msg="Valor del campo <b>Fecha</b> debe corresponder a un <i>lunes</i> de la semana", title="Error de Fecha")


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
def crear_orden_de_compra(est_name):
	estimacion = frappe.get_doc("Estimacion de Compras", est_name)

	if not estimacion.docstatus == 1:
		frappe.throw("¡Estimacion no validada... por favor, presente el documento para confirmar!")
		
	order = frappe.new_doc("Purchase Order")

	# defaults
	order.total = 0
	order.created_from = est_name
	order.transaction_date = estimacion.date
	order.supplier = estimacion.supplier
	order.supplier_rnc = frappe.get_value("Supplier", estimacion.supplier, "rnc")

	for sku in estimacion.items:
		detalle = frappe.get_doc("Detalle de Estimacion", sku.codigo)
		item = frappe.get_doc("Item", detalle.sku)

		# default values
		schedule_date = frappe.utils.add_days(detalle.date, (detalle.transit_weeks * 7))
		defaults = frappe.utils.get_defaults()
		amount = float(item.standard_rate) * float(detalle.order_sku_total)
		order.total += amount

		# append the values
		order.append("items", {
			"item_code" : item.item_code,
			"item_name" : item.item_name,
			"schedule_date" : schedule_date,
			"description": item.description,
			"qty": detalle.order_sku_total,
			"stock_uom": item.stock_uom,
			"uom": item.stock_uom,
			"conversion_factor": 1,
			"warehouse": defaults.warehouse,
			"rate": item.standard_rate,
			"amount": amount,
			"base_rate": item.standard_rate,
			"base_amount": amount,
		})
	
	# order.insert()

	return order.as_dict()

@frappe.whitelist()
def existe_orden_de_compra(estimacion):
	order_list = frappe.get_list("Purchase Order",
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
