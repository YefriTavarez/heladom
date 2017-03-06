# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe, json
from datetime import datetime

weeks_in_year = 52 #Weeks a year has

@frappe.whitelist()
def get_final_order_stock(year, week, sku):	
	stock = frappe.db.sql("""
		SELECT SUM(child.onces_total)
		FROM `tabInventario Fisico Helados Items` AS child 
		JOIN `tabInventario Fisico Helados` AS parent 
		ON child.parent = parent.name 
		WHERE child.sku = '%(sku)s' 
		AND parent.year = '%(year)s' 
		AND parent.week = '%(week)s'"""
	% { "sku" : sku, "year" : year, "week" : week })

	if stock[0][0]:
		return float(stock[0][0])

	return float(0)


@frappe.whitelist()
def get_total_in_transit(sku):	
	total = frappe.db.sql("""
		SELECT SUM(order_sku_total)
		FROM `tabEstimacion de Compra`		
		WHERE sku = '%(sku)s' 
		AND was_received <> 1
		AND docstatus = 1"""
	% { "sku" : sku })

	if total[0][0]:
		return float(total[0][0])

	return float(0)


@frappe.whitelist()
def get_average(start_date, end_date, sku):
	start_date = remove_date_dot(start_date)
	end_date = remove_date_dot(end_date)

	frappe.db.sql(
		"""CALL GetPromedioHistorico('%(from_date)s', '%(to_date)s', '%(sku)s', @average)""" 
			% { "from_date" : start_date, "to_date" : end_date, "sku" : sku })

	average = frappe.db.sql("""SELECT @average""")[0][0]

	if not average:
		return float(0)

	return round(average, 2)

def remove_date_dot(date_str):
	if date_str.split("."):
		return date_str.replace(".","")

	return date_str

@frappe.whitelist()
def get_sku_list(supplier, sku_group=None):
	return frappe.db.sql("""
		SELECT sku.name sku, sku.item sku_name, sku.able_to_estamation, sku.available_locally, sku.pieces_per_level, 
			sku.rotation_key, sku.code, sku.pieces_per_pallet, sku.arancel, sku.generic
		FROM tabSKU AS sku 
		JOIN tabItem AS item 
		ON sku.item = item.name 
		WHERE item.default_supplier = '%(default_supplier)s'
		AND sku.able_to_estamation = 1 %(filter)s"""
	% { "default_supplier": supplier, "filter": get_filters(sku_group) }, as_dict=True)

def get_filters(sku_group):
	if sku_group:
		return "AND item.item_group = '{0}'".format(sku_group)

	return ""

@frappe.whitelist()
def get_week(date):
	"""Returns the year week from a date in the format ####.## where #### is the year and ## is the year week"""
	week = str(date).split(".")[1]

	if int(week) > weeks_in_year:
		week = weeks_in_year

	if int(week) < 1:
		week = 1

	return week

@frappe.whitelist()
def get_year(date):
	"""Returns the year from a date in the format ####.## where #### is the year and ## is the year week"""
	return str(date).split(".")[0]

@frappe.whitelist()
def add_weeks(date, weeks=1):
	"""Adds the number of weeks to the specified date. 
		If not specified it adds only one week."""
	cur_year = get_year(date)
	next_year_date = add_years(date)
	next_year = get_year(next_year_date)
	week = get_week(date)
	
	weeks = abs(int(weeks)) #to make sure we are handling good dates

	if int(weeks) > 52:
		left_weeks = int(weeks) % weeks_in_year
		years_ahead = int(weeks) // weeks_in_year
		new_week = int(week) + int(left_weeks)

		if new_week > weeks_in_year:
			new_week = int(new_week) - weeks_in_year
			cur_year = next_year

		tmp_date = "{0}.{1}".format(cur_year, new_week)
		
		return add_years(tmp_date, years_ahead)

	new_week = int(week) + int(weeks)
	
	if new_week > weeks_in_year:
		new_week = new_week - weeks_in_year
		cur_year = next_year
		
	return "{0}.{1}".format(cur_year, new_week)

@frappe.whitelist()
def subtract_weeks(date, weeks=1):
	"""Subtracts the number of weeks to the specified date.
		If not specified it subtracts only one week."""
	cur_year = get_year(date)
	last_year_date = subtract_years(date)
	last_year = get_year(last_year_date)
	week = get_week(date)
	
	weeks = abs(int(weeks)) #to make sure we are handling good dates
	if int(weeks) > 52:
		left_weeks = int(weeks) % weeks_in_year
		years_back = int(weeks) // weeks_in_year
		new_week = int(week) - int(left_weeks)

		if new_week < 1:
			new_week = weeks_in_year - abs(new_week)
			cur_year = last_year

		tmp_date = "{0}.{1}".format(cur_year, new_week)
		
		return subtract_years(tmp_date, years_back)

	new_week = int(week) - int(weeks)
	
	if new_week < 1:
		new_week = weeks_in_year - abs(new_week)
		cur_year = last_year
		
	return "{0}.{1}".format(cur_year, new_week)

@frappe.whitelist()
def add_years(date, years=1):
	week = get_week(date)
	cur_year = get_year(date)
	next = int(cur_year) + int(years)
	return "{0}.{1}".format(next, week)

@frappe.whitelist()
def subtract_years(date, years=1):
	week = get_week(date)
	cur_year = get_year(date)
	last = int(cur_year) - int(years)
	return "{0}.{1}".format(last, week)

@frappe.whitelist()
def fetch_as_array(date, weeks):
	operate_weeks = add_weeks if weeks > 0 else subtract_weeks

	absolute_weeks = abs(weeks) # To make sure we are handling good values
	array = range(0, absolute_weeks)

	dates_array = []
	for week in array:
		dates_array.append(
			operate_weeks(date, week)
		)

	return dates_array



@frappe.whitelist()
def subtract_one(value):
	return int(value) - 1 