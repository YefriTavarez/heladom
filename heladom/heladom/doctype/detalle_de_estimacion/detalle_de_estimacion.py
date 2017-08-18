# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe, heladom.api
from frappe.model.document import Document
from heladom.constants import WEEK_DAYS, ONE_YEAR, WEEK_DAY_SET

day = frappe.db.get_single_value("Configuracion", "default_week_day", cache=False)
week_day = [e.get("label") for e in WEEK_DAY_SET if e.get("value") == str(day)][0]

class DetalledeEstimacion(Document):
	def calculate_dates(self):
		from heladom.api import add_weeks, add_years, add_days
		heladom.api.validate_current_date(self.date, day, week_day)

		cutoff_trend = int(self.cut_trend)
		self.recent_history_current_year_start_date = add_weeks(self.date, -cutoff_trend + 1) # usually 10 weeks back
		self.recent_history_current_year_end_date = str(self.date) # current period

		self.recent_history_last_year_start_date = add_years(self.recent_history_current_year_start_date, -ONE_YEAR) #to go a year back
		self.recent_history_last_year_end_date = add_years(self.recent_history_current_year_end_date, -ONE_YEAR) #to go a year back

		transit_weeks = int(self.transit_weeks)
		self.transit_period_start_date = add_days(self.recent_history_last_year_end_date, +WEEK_DAYS)
		self.transit_period_end_date = add_weeks(self.recent_history_last_year_end_date, +transit_weeks)

		consumption_weeks = int(self.consumption_weeks)
		self.consumption_period_start_date = add_days(self.transit_period_end_date, +WEEK_DAYS)
		self.consumption_period_end_date = add_weeks(self.transit_period_end_date, +consumption_weeks)
		

	def set_missing_values(self):
		self.calculate_dates()
		self.fill_tables()

		from heladom.api import get_average

		##### SECCION HISTORIA RECIENTE ######

		self.current_year_avg = get_average(
			self.recent_history_current_year_start_date,
			self.recent_history_current_year_end_date,
			self.sku
		)

		self.last_year_avg = get_average(
			self.recent_history_last_year_start_date,
			self.recent_history_last_year_end_date,
			self.sku
		)

		trend_tmp = 1 #to avoid issues
		try:
			trend_tmp = float(self.current_year_avg) / float(self.last_year_avg)
		except ZeroDivisionError as e:
			frappe.errprint(e)

		decimal_trend = float(trend_tmp - 1)
		trend = (decimal_trend * 100)
		self.tendency = round(trend, 2)

		##### SECCION PERIODO EN TRANSITO ######

		self.desp_avg = get_average(
			self.transit_period_start_date, 
			self.transit_period_end_date,
			self.sku
		)

		self.recent_tendency = self.tendency

		self.total_required = float(self.desp_avg) * float(self.transit_weeks)

		real_required = self.total_required + (self.total_required * decimal_trend)
		self.real_required = round(real_required, 2)
		
		self.type = "Solo Tend Despacho"

		##### SECCION PERIODO DE USO ######
		from heladom.api import get_final_order_stock
		
		self.avg_use_period = get_average(
			self.consumption_period_start_date, 
			self.consumption_period_end_date, 
			self.sku
		)

		self.consumption__use_period = int(self.consumption_weeks)
		total_reqd_use_period = float(self.avg_use_period) * self.consumption__use_period
		self.total_reqd_use_period = round(total_reqd_use_period)

		self.order_sku_existency = get_final_order_stock(self.date, self.sku)

		tendency__use_period = float(self.presup_gral) / 100
		self.tendency__use_period = self.presup_gral
		real_reqd_use_period = self.total_reqd_use_period * (1 + tendency__use_period)
		self.real_reqd_use_period = round(real_reqd_use_period, 2)

		self.trasit_weeks = self.transit_weeks
		self.type_use_period = "Presupuesto General"

		##### SECCION ORDEN FINAL ######
		from heladom.api import get_total_in_transit

		self.general_coverage = int(self.coverage_weeks)
		self.reqd_option_1 = round(self.general_coverage * self.current_year_avg)
		self.reqd_option_2 = round(self.total_required + self.total_reqd_use_period)
		self.reqd_option_3 = round(self.real_required + self.real_reqd_use_period)

		self.order_sku_in_transit = get_total_in_transit(self.sku)
		self.required_qty = 3 #set the option number three

		order_sku_real_reqd = self.reqd_option_3 - self.order_sku_existency - self.order_sku_in_transit
		self.order_sku_real_reqd = round(order_sku_real_reqd)
		self.order_sku_total = self.order_sku_real_reqd

		self.piece_by_level = frappe.db.get_value("Item", self.sku, "units_in_level")
		self.piece_by_pallet = frappe.db.get_value("Item", self.sku, "units_in_pallet")

		if self.piece_by_level:
			self.level_qty = float(self.order_sku_total) / float(self.piece_by_level)

		if self.piece_by_pallet:
			self.pallet_qty = float(self.order_sku_total) / float(self.piece_by_pallet)

	def fill_tables(self):
		from heladom.api import fetch_as_array

		self.current_period_table = []
		self.previous_period_table = []
		self.transit_period_table = []
		self.usage_period_table = []

		trend_weeks = int(self.cut_trend)
		transit_weeks = int(self.transit_weeks)
		consumption_weeks = int(self.consumption_weeks)

		trend_date_as_array = fetch_as_array(self.recent_history_current_year_start_date, trend_weeks)

		for trend_week in trend_date_as_array:
			self.append("current_period_table", 
				self.get_physical_stock_as_dict(trend_week, self.sku)
			)

		prev_date_as_array = fetch_as_array(self.recent_history_last_year_start_date, trend_weeks)

		for previous_week in prev_date_as_array:    
			self.append("previous_period_table",
				self.get_physical_stock_as_dict(previous_week, self.sku)
			)

		transit_date_as_array = fetch_as_array(self.transit_period_start_date, transit_weeks)

		for transit_week in transit_date_as_array:
			self.append("transit_period_table", 
				self.get_physical_stock_as_dict(transit_week, self.sku)
			)

		usage_date_as_array = fetch_as_array(self.consumption_period_start_date, consumption_weeks)

		for usage_week in usage_date_as_array:
			self.append("usage_period_table", 
				self.get_physical_stock_as_dict(usage_week, self.sku)
			)

	def get_physical_stock_as_dict(self, date, sku):
		import heladom.api

		row = frappe.db.sql("""SELECT parent.date AS ciclo, child.consumo AS desp, child.onces_total AS exist
			FROM 
				`tabInventario Fisico Helados` AS parent 
			JOIN 
				`tabInventario Fisico Helados Items` AS child 
			ON 
				parent.name = child.parent 
			WHERE
				child.sku = '%(sku)s' 
			AND 
				parent.date = '%(date)s'""" 
		% {"date": date, "sku" : sku}, as_dict=True)

		if not row:
			return { "ciclo": 0, "desp": 0, "exist":0 }
		
		return heladom.api.first(row)
	