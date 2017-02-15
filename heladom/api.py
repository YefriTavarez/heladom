# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe, json
from datetime import datetime
from heladom.doctype.estimacion_de_compra.estimacion_de_compra import validate_fields

@frappe.whitelist()
def get_estimation_info(doc):
	doc = json.loads(doc)
	now = datetime.now()

	validate_fields(doc)

	posting_date = doc['date']
	old_end_date = doc["cut_trend_week"]
	old_start_date = doc["date_cut_trend"]
	supplier = doc["supplier"]
	cost_center = doc["cost_center"]
	cut_trend = doc["cut_trend"]	
	estimation_type = doc["estimation_type"]
	presup_gral = doc["presup_gral"]
	transit_weeks = doc["transit"]
	consumption_weeks = doc["consumption"]
	
	weeks_in_year = 52
	current_year = posting_date.split("-")[0]
	last_year = int(current_year) - 1
	before_last_year = int(current_year) - 1

	transit_period_start_date = old_start_date.replace(".", "")
	transit_period_end_date = old_end_date.replace(".", "")

	recent_history_start_week = int(old_start_date.split(".")[1])-10
	recent_history_end_week = int(old_start_date.split(".")[1])-1

	recent_history_start_year = old_start_date.split(".")[0]
	recent_history_end_year = old_start_date.split(".")[0]

	if recent_history_start_week < 0:
		recent_history_start_week = weeks_in_year - abs(recent_history_start_week)
		recent_history_start_year = before_last_year - 1

	if recent_history_end_week < 0:
		recent_history_end_week = weeks_in_year - abs(recent_history_end_week)
		recent_history_end_year = before_last_year - 1


	current_start_date = "{0}{1}".format(recent_history_start_year, recent_history_start_week) 
	current_end_date = "{0}{1}".format(recent_history_end_year, recent_history_end_week) 

	last_year_transit_start_date = "{0}{1}".format(int(recent_history_start_year) - 1, recent_history_start_week) 
	last_year_transit_end_date = "{0}{1}".format(int(recent_history_end_year) - 1, recent_history_end_week)

	consumption_period_start_week = int(old_end_date.split(".")[1]) + 1
	consumption_period_end_week = int(old_end_date.split(".")[1]) + int(consumption_weeks)

	consumption_period_start_year = old_start_date.split(".")[0]
	consumption_period_end_year = old_start_date.split(".")[0]

	if consumption_period_start_week > weeks_in_year:
		consumption_period_start_week = consumption_period_start_week - weeks_in_year
		consumption_period_start_year = consumption_period_start_year + 1

	if consumption_period_end_week > weeks_in_year:
		consumption_period_end_week = consumption_period_end_week - weeks_in_year
		consumption_period_end_year = consumption_period_end_year + 1

	last_year_consumption_start_date = "{0}{1}".format(consumption_period_start_year, consumption_period_start_week)
	last_year_consumption_end_date = "{0}{1}".format(consumption_period_end_year, consumption_period_end_week)


	sql = frappe.db.sql("""SELECT * FROM tabSKU""", as_dict=1)


	result = []
	for sku in sql:
		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (transit_period_start_date, transit_period_end_date ,sku.name,))
		sku.last_year_transit_avg = frappe.db.sql("""select @prom""")[0][0]
		#sku.last_year_avg = last_avg
		frappe.errprint("transit_period_start_date: {0}".format(transit_period_start_date))
		frappe.errprint("transit_period_end_date: {0}".format(transit_period_end_date))

		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (current_start_date, current_end_date ,sku.name,))
		sku.current_year_avg = frappe.db.sql("""select @prom""")[0][0]
		frappe.errprint("current_start_date: {0}".format(current_start_date))
		frappe.errprint("current_end_date: {0}".format(current_end_date))

		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (last_year_transit_start_date, last_year_transit_end_date ,sku.name,))
		sku.last_year_avg = frappe.db.sql("""select @prom""")[0][0]
		frappe.errprint("last_year_transit_start_date: {0}".format(last_year_transit_start_date))
		frappe.errprint("last_year_transit_end_date: {0}".format(last_year_transit_end_date))

		frappe.db.sql("""CALL GetPromedioHistorico('%s','%s','%s',@prom)""" % (last_year_consumption_start_date, last_year_consumption_end_date ,sku.name,))
		sku.last_year_consumption_avg = frappe.db.sql("""select @prom""")[0][0]
		frappe.errprint("last_year_consumption_start_date: {0}".format(last_year_consumption_start_date))
		frappe.errprint("last_year_consumption_end_date: {0}".format(last_year_consumption_end_date))

		sku.final_order_stock = get_final_order_stock(sku.name, recent_history_end_year, recent_history_end_week)

		result.append(sku)

	return result

def get_final_order_stock(sku, year, week):
	frappe.errprint("sku: {0}".format(sku))
	frappe.errprint("year: {0}".format(year))
	frappe.errprint("week: {0}".format(week))
	
	stock = frappe.db.sql("""SELECT onces_total 
		FROM `tabInventario Fisico Helados Items` AS child 
		JOIN `tabInventario Fisico Helados` AS parent 
		ON child.parent = parent.name 
		WHERE child.sku = '%s' 
		AND parent.year = '%s' 
		AND parent.week = '%s'"""
		% (sku, year, week,), 
	as_dict=True)

	if stock:
		return stock[0].onces_total

	return 0

