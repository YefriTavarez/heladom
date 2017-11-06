# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from constants import ZERO, DRAFT, SUBMITTED, CANCELLED, MONDAY, WEEK_DAYS, WEEKS_IN_YEAR

from frappe.utils import flt

def get_final_order_stock(date, sku, cost_center=None):
	"""
	Returns the last stock balance for an Item from in an specific date

	:params date: The specific of the date
	:params sku: The Item name which is getting the balance for
	:params cost_center: An optional argument for filtering by the Cost Center
	"""

	filters = ("AND centro_de_costo = '%(cost_center)s'" % cost_center) \
		if cost_center else ""
	
	stock = frappe.db.sql("""SELECT SUM(existencia)
		FROM `tabRetail Food Ledger` 
		WHERE sku = '%(sku)s' 
		AND fecha_transacion = '%(date)s' %(filters)s"""
	% { "sku" : sku, "date" : date, "filters": filters })

	conversion_factor = frappe.get_value("UOM Conversion Detail", {
		"parent": sku,
		"generico": "1",
	}, ["conversion_factor"])

	if stock and stock[ZERO]:
		return flt(stock[ZERO][ZERO]) / flt(conversion_factor)

	return flt(ZERO)

def get_last_stock(date, sku, cost_center):
	"""
	Returns the last stock balance for an Item from in an specific date

	It's the same as `get_final_order_stock` but with only difference that this one returns only one value
	and the former returns the SUM of all the records found in case there's more than one. This is useful when dealing with
	the Estimacion de Compras which is for all the Cost Centers rather than just one.

	:params date: The specific of the date
	:params sku: The Item name which is getting the balance for
	:params cost_center: An optional argument for filtering by the Cost Center
	"""
	stock = frappe.db.sql("""SELECT existencia
		FROM `tabRetail Food Ledger` 
		WHERE sku = '%(sku)s' 
		AND fecha_transacion = '%(date)s'
		AND centro_de_costo = '%(cost_center)s'"""
	% { "sku" : sku, "date" : date, "cost_center": cost_center })

	conversion_factor = frappe.get_value("UOM Conversion Detail", {
		"parent": sku,
		"generico": "1",
	}, ["conversion_factor"])

	if stock and stock[ZERO]:
		return flt(stock[ZERO][ZERO]) / flt(conversion_factor)

	return flt(ZERO)

def get_total_in_transit(sku, cost_center=None):

	filters = " AND cost_center = '%s'" % cost_center

	filters = not cost_center and ""
	total = frappe.db.sql("""SELECT SUM(order_sku_total)
		FROM `tabDetalle de Estimacion`     
		WHERE sku = '%(sku)s' 
		AND was_received <> 1
		AND docstatus = %(submitted)s
		%(filters)s"""
	% { "sku" : sku, "submitted": SUBMITTED, "filters": filters})

	if total and total[ZERO]:
		return flt(total[ZERO][ZERO])

	return flt(ZERO)

def get_total_not_received(sku, cost_center):  
	total = frappe.db.sql("""SELECT SUM(order_sku_total)
		FROM `tabDetalle de Pedido`     
		WHERE sku = '%(sku)s' 
		AND was_received <> 1
		AND cost_center = '%(cost_center)s'
		AND docstatus = %(submitted)s"""
	% { "sku" : sku, "cost_center": cost_center, "submitted": SUBMITTED})

	if total and total[ZERO]:
		return flt(total[ZERO][ZERO])

	return flt(ZERO)

def get_average(start_date, end_date, sku, cost_center=None):
	"""
	Returns the AVERAGE for an Item from within an specific date

	:params start_date: The Start of the date range
	:params end_date: The ending of the date range
	:params sku: The Item name which is getting averaged
	:params cost_center: An optional argument for filtering by the Cost Center
	"""

	if not sku:
		frappe.throw("Falta el SKU")

	conversion_factor = frappe.get_value("UOM Conversion Detail", {
		"parent": sku,
		"generico": "1",
	}, ["conversion_factor"])

	filters = "AND centro_de_costo = '%s'" % cost_center

	average = frappe.db.sql("""SELECT AVG(consumo)
		FROM `tabRetail Food Ledger`
		WHERE 
			fecha_transacion 
				BETWEEN '%(start_date)s' AND '%(end_date)s'
			AND sku = '%(sku)s'
			AND consumo > 0.000 %(filters)s""" 
		% {
			"start_date": start_date,
			"end_date": end_date,
			"sku": sku,
			"filters": filters if cost_center else ""
		})


	if not conversion_factor:
		frappe.throw("""Falta Factor de Conversion para la unidad minima en el Generico en el Item {0}""".format(sku))

	promedio_unidad_minima = flt(average[0][0])
	
	return flt(promedio_unidad_minima / conversion_factor, 2)



def get_sku_list(supplier, sku_group=None):

	# set the filters if the sku_group is set
	filters = { "item_group": sku_group } if sku_group else { }

	# return the results
	return frappe.get_list(doctype="Item", fields="*", filters=filters)

def validate_current_date(date, weekday, str):
	from datetime import datetime

	dateobj = datetime.strptime(date,"%Y-%m-%d") if isinstance(date, basestring) else date
	if not dateobj.isoweekday() == int(weekday):
		frappe.throw("La Fecha debe corresponder a un {0} de la semana".format(str))


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
def crear_orden_de_compra(source):
	estimacion = frappe.get_doc("Estimacion de Compras", source)

	if not estimacion.docstatus == 1:
		frappe.throw("¡Estimacion no validada... por favor, presente el documento para confirmar!")
		
	order = frappe.new_doc("Purchase Order")

	# defaults
	order.total = 0
	order.created_from = source
	order.transaction_date = estimacion.date
	order.supplier = estimacion.supplier
	order.supplier_rnc = frappe.get_value("Supplier", estimacion.supplier, "rnc")

	filters = { "parent": estimacion.name, "docstatus": ["!=", "2"] }
	for sku in frappe.get_list("Detalle de Estimacion", filters):
		detalle = frappe.get_doc("Detalle de Estimacion", sku.name)
		item = frappe.get_doc("Item", detalle.sku)

		# default values
		schedule_date = frappe.utils.add_days(detalle.date, (detalle.transit_weeks * 7))
		defaults = frappe.utils.get_defaults()
		amount = flt(item.standard_rate) * flt(detalle.order_sku_total)
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
	
	return order.as_dict()

@frappe.whitelist()
def validate_estimation_date(date):
	from constants import WEEK_DAY_SET
	
	day = frappe.db.get_single_value("Configuracion", "default_week_day", cache=False)
	week_day = [e.label for e in WEEK_DAY_SET if e.value == str(day)][0]

	validate_current_date(date, day, week_day)

@frappe.whitelist()
def validate_pedido_date(date):
	from constants import WEEK_DAY_SET
	
	day = frappe.db.get_single_value("Configuracion", "default_week_day_", cache=False)
	week_day = [e.label for e in WEEK_DAY_SET if e.value == str(day)][0]

	validate_current_date(date, day, week_day)

@frappe.whitelist()
def crear_solicitud_de_materiales(source):
	pedido = frappe.get_doc("Pedido en Linea", source)

	if not pedido.docstatus == 1:
		frappe.throw("¡Pedido no validado... por favor, presente el documento para confirmar!")
		
	mreq = frappe.new_doc("Material Request")

	# defaults
	mreq.total = 0
	mreq.created_from = source
	mreq.transaction_date = pedido.date
	mreq.supplier = pedido.supplier
	mreq.supplier_rnc = frappe.get_value("Supplier", pedido.supplier, "rnc")

	filters = { "parent": pedido.name, "docstatus": ["!=", "2"] }
	for sku in frappe.get_list("Detalle de Estimacion", filters):
		detalle = frappe.get_doc("Detalle de Estimacion", sku.name)
		item = frappe.get_doc("Item", detalle.sku)

		# default values
		schedule_date = frappe.utils.add_days(detalle.date, (detalle.transit_weeks * 7))
		defaults = frappe.utils.get_defaults()
		amount = flt(item.standard_rate) * flt(detalle.order_sku_total)
		mreq.total += amount

		# append the values
		mreq.append("items", {
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
	
	return mreq.as_dict()

@frappe.whitelist()
def existe_orden_de_compra(estimacion):
	return frappe.get_list("Purchase Order",
		fields=["name"],
		filters={
			"created_from": estimacion,
			"docstatus": ["!=", CANCELLED]
		}, as_dict=True
	)


@frappe.whitelist()
def existe_solicitud_de_materiales(pedido):
	return frappe.get_list("Material Request",
		fields=["name"],
		filters={
			"created_from": pedido,
			"docstatus": ["!=", CANCELLED]
		}, as_dict=True
	)

def first(array):
	if not array:
		array.append(flt(ZERO))

	return array[ZERO]

@frappe.whitelist()
def get_stock_uom_conversion_rate(item, uom):
	frappe.errprint("item {}".format(item))
	frappe.errprint("uom {}".format(uom))
	result = frappe.db.sql(
		"""SELECT
			child.conversion_factor 
		FROM
			`tabUOM Conversion Detail` AS child 
			JOIN
				tabItem AS parent 
				ON parent.name = child.parent 
		WHERE
			parent.name = %s
			AND child.uom = %s
		""", (item, uom),
	as_dict=False)

	if len(result):
		frappe.errprint("result[0][0] {}".format(result[0][0]))
		return result[0][0]

	frappe.errprint("0.000 {}".format(0.000))
	return 0.000

@frappe.whitelist()
def get_stock_balance(warehouse, item_code):
	result = frappe.db.sql("""SELECT SUM(actual_qty)
		FROM
    		`tabStock Ledger Entry` 
		WHERE
    		warehouse = %s
    	AND item_code = %s
	""", (warehouse, item_code), as_dict=False)[0][0]

	return result