# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe, json, datetime
from frappe.model.document import Document

class EstimaciondeCompra(Document):
	def before_submit(self):
		# Crear una entrada en administrador de pedidos
		if self.is_warehouse_transfer:
			pedido = frappe.get_doc({
					"doctype": "Administrador de Pedidos",
					"date": self.date,
					"estimation": self.name,
					"cost_center": self.cost_center
					})

			for sku in self.estimation_skus:
				pedido.append("skus", {
					"doctype": "Pedido Skus",
					"sku": sku.sku,
					"sku_name": sku.sku_name,
					"qty": sku.order_sku_total
				})

			pedido.insert()

	def get_estimation_info(self):
		from heladom.api import get_sku_list
		self.validate_fields()
		frappe.msgprint("¡Proceso Iniciado!")

		self.calculate_dates()

		self.estimation_skus = []

		for sku in get_sku_list(self.supplier, self.estimation_type):
			sku = self.set_missing_values(sku)
			self.append("estimation_skus", sku)

	def validate_fields(self):
		from frappe import throw

		if not self.cost_center: throw("¡Falta <b>Centro de costo</b>!")
		if not self.supplier: throw("¡Falta <b>Suplidor</b>!")
		if not self.cut_trend: throw("¡Falta <b>Corte de Tendencia</b>!")
		if not self.presup_gral: throw("¡Falta <b>Presupuesto General</b>!")			
		if not self.date_cut_trend: throw("¡Falta <b>Fecha Inicio</b>!")
		if not self.transit: throw("¡Falta Semanas en <b>Transito</b>!")
		if not self.consumption: throw("¡Falta Semanas de <b>Consumo</b>!")
		if not self.coverage: throw("¡Falta Semanas de <b>Cobertura</b>!")
		if not self.date: throw("¡Falta <b>Fecha</b>!")
	
	def calculate_dates(self):
		from heladom.api import get_year, get_week

		self.cur_year = get_year(self.date_cut_trend)
		self.cur_week = get_week(self.date_cut_trend)
		
		from heladom.api import subtract_one
		
		trend_weeks = subtract_one(self.cut_trend) #to match the weeks
		transit_weeks = subtract_one(self.transit)  #to match the weeks
		consumption_weeks = subtract_one(self.consumption) #to match the weeks

		from heladom.api import subtract_weeks
		
		self.recent_history_current_year_start_date = subtract_weeks(self.date_cut_trend, trend_weeks)
		self.recent_history_current_year_end_date = self.date_cut_trend

		from heladom.api import subtract_years

		self.recent_history_last_year_start_date = subtract_years(self.recent_history_current_year_start_date)
		self.recent_history_last_year_end_date = subtract_years(self.date_cut_trend)

		from heladom.api import add_weeks

		self.transit_period_start_date = add_weeks(self.recent_history_last_year_end_date)
		self.transit_period_end_date = add_weeks(self.transit_period_start_date, transit_weeks)

		self.consumption_period_start_date = add_weeks(self.transit_period_end_date)
		self.consumption_period_end_date = add_weeks(self.consumption_period_start_date, consumption_weeks)

	def set_missing_values(self, sku):
		from heladom.api import get_average

		###### SECCION HISTORIA RECIENTE ######

		sku.current_year_avg = get_average(
			self.recent_history_current_year_start_date,
			self.recent_history_current_year_end_date,
			sku.sku
		)

		sku.last_year_avg = get_average(
			self.recent_history_last_year_start_date,
			self.recent_history_last_year_end_date,
			sku.sku
		)

		trend_tmp = float(sku.current_year_avg) / float(sku.last_year_avg)
		decimal_trend = float(trend_tmp - 1)
		trend = (decimal_trend * 100) #abs ?
		sku.tendency = round(trend, 2)

		###### SECCION PERIODO EN TRANSITO ######

		sku.desp_avg = get_average(
			self.transit_period_start_date, 
			self.transit_period_end_date,
			sku.sku
		)

		sku.recent_tendency = sku.tendency

		sku.total_required = float(sku.desp_avg) * float(self.transit)

		real_required = sku.total_required + (sku.total_required * decimal_trend)
		sku.real_required = round(real_required, 2)
		
		sku.type = "Solo Tend Despacho"

		###### SECCION PERIODO DE USO ######
		from heladom.api import get_final_order_stock
		
		sku.avg_use_period = get_average(
			self.consumption_period_start_date, 
			self.consumption_period_end_date, 
			sku.sku
		)

		sku.consumption__use_period = int(self.consumption)
		total_reqd_use_period = float(sku.avg_use_period) * sku.consumption__use_period
		sku.total_reqd_use_period = round(total_reqd_use_period)

		sku.order_sku_existency = get_final_order_stock(self.cur_year, self.cur_week, sku.sku)

		tendency__use_period = float(self.presup_gral) / 100
		sku.tendency__use_period = self.presup_gral
		real_reqd_use_period = sku.total_reqd_use_period * (1 + tendency__use_period)
		sku.real_reqd_use_period = round(real_reqd_use_period, 2)

		current_period_average = get_average(self.date_cut_trend, self.date_cut_trend, sku.name)
		sku.trasit_weeks = self.transit
		sku.type_use_period = "Presupuesto General"

		###### SECCION ORDEN FINAL ######
		from heladom.api import get_total_in_transit

		sku.general_coverage = int(self.coverage)
		sku.reqd_option_1 = round(sku.general_coverage * sku.current_year_avg)
		sku.reqd_option_2 = round(sku.total_required + sku.total_reqd_use_period)
		sku.reqd_option_3 = round(sku.real_required + sku.real_reqd_use_period)

		sku.order_sku_in_transit = get_total_in_transit(sku.sku)
		sku.required_qty = 3 #set the option number three

		order_sku_real_reqd = sku.reqd_option_3 - sku.order_sku_existency - sku.order_sku_in_transit
		sku.order_sku_real_reqd = round(order_sku_real_reqd)
		sku.order_sku_total = sku.order_sku_real_reqd

		sku.piece_by_level = sku.pieces_per_level
		sku.piece_by_pallet = sku.pieces_per_pallet

		sku.level_qty = float(sku.order_sku_total) / float(sku.piece_by_level)
		sku.pallet_qty = float(sku.order_sku_total) / float(sku.piece_by_pallet)

		return sku

	def fill_tables(self, sku):
		from heladom.api import get_week, get_year
		from heladom.api import subtract_weeks
		from heladom.api import subtract_one

		self.calculate_dates()
		self.recent_history = []
		self.transit_period = []
		self.usage_period = []

		for trend_week in range(0, self.cut_trend):

			trend_date = subtract_weeks(self.date_cut_trend, trend_week)
			cur_year = get_year(trend_date)
			last_year = subtract_one(cur_year)
			week = get_week(trend_date)

			cur_fields_dict = self.get_physical_stock_as_dict(cur_year, week, sku)
			last_fields_dict = self.get_physical_stock_as_dict(last_year, week, sku)

			self.recent_history.append({
				"anterior_ciclo" : last_fields_dict.year_week,
				"anterior_consm" : last_fields_dict.consumo,
				"anterior_exist" : last_fields_dict.onces_total,
				"vigente_consm" : cur_fields_dict.consumo,
				"vigente_exist" : cur_fields_dict.onces_total
			})



		from heladom.api import add_weeks

		transit_start_date = add_weeks(self.date_cut_trend)

		for trend_week in range(0, self.transit):
			transit_date = add_weeks(transit_start_date, trend_week)

			cur_year = get_year(transit_date)
			last_year = subtract_one(cur_year)
			week = get_week(transit_date)
			transit_fields_dict = self.get_physical_stock_as_dict(last_year, week, sku)

			self.transit_period.append({
				"ciclo" : transit_fields_dict.year_week,
				"desp" : transit_fields_dict.consumo,
				"exist" : transit_fields_dict.onces_total,
			})

		usage_start_date = add_weeks(transit_start_date, self.transit)

		for usage_week in range(0, self.consumption):
			usage_date = add_weeks(usage_start_date, usage_week)

			cur_year = get_year(usage_date)
			last_year = subtract_one(cur_year)
			week = get_week(usage_date)
			usage_fields_dict = self.get_physical_stock_as_dict(last_year, week, sku)

			self.usage_period.append({
				"ciclo" : usage_fields_dict.year_week,
				"desp" : usage_fields_dict.consumo,
				"exist" : usage_fields_dict.onces_total,
			})

	def get_physical_stock_as_dict(self, year, week, sku):
		row = frappe.db.sql("""SELECT parent.year_week, child.name, child.consumo, child.onces_total
			FROM `tabInventario Fisico Helados` AS parent 
			JOIN `tabInventario Fisico Helados Items` AS child 
			ON parent.name = child.parent 
			WHERE child.sku = '%(sku)s' 
			AND parent.year='%(year)s' 
			AND parent.week='%(week)s'""" 
		% {"year":year, "week":week, "sku":sku}, as_dict=True)

		if not row:
			frappe.throw("¡No se encontro el SKU <b>{2}</b> para la semana {0}.{1}!"
				.format(year, week, sku))

		return row[0]