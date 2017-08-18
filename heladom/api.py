# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from constants import ZERO, DRAFT, SUBMITTED, CANCELLED, MONDAY, WEEK_DAYS, WEEKS_IN_YEAR

def get_final_order_stock(date, sku):   
    stock = frappe.db.sql("""SELECT SUM(existencia)
        FROM `tabRetail Food Ledger` 
        WHERE sku = '%(sku)s' 
        AND fecha_transacion = '%(date)s'"""
    % { "sku" : sku, "date" : date })

    generico = frappe.get_value("Item", sku, "generic")
    from_uom = frappe.get_value("Item", sku, "stock_uom")
    to_uom = frappe.get_value("Generico", generico, "uom")
    # frappe.errprint("from_uom %s" % from_uom)
    # frappe.errprint("to_uom %s" % to_uom)

    conversion_factor = frappe.get_value("Factor de Conversion", {
        "parent": sku,
        "from_uom": from_uom,
        "to_uom": to_uom
    }, ["conversion_factor"])

    if stock[ZERO][ZERO]:
        return float(stock[ZERO][ZERO]) * float(conversion_factor)

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


def get_average(start_date, end_date, sku, cost_center=None):
    generico = frappe.get_value("Item", sku, "generic")
    to_uom = frappe.get_value("Generico", generico, "uom")
    from_uom = frappe.get_value("Item", sku, "stock_uom")
    # frappe.errprint("from_uom %s" % from_uom)
    # frappe.errprint("to_uom %s" % to_uom)

    conversion_factor = frappe.get_value("Factor de Conversion", {
        "parent": sku,
        "from_uom": from_uom,
        "to_uom": to_uom
    }, ["conversion_factor"])
    # frappe.errprint("conversion_factor %s" % conversion_factor)
    # frappe.errprint("conversion_factor %s" % conversion_factor)

    filters = "centro_de_costo = '%s'" % cost_center

    consumo_list = frappe.db.sql("""SELECT consumo 
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
        }, 
    as_dict=True)

    sumatoria = 0.000

    for current in consumo_list:
        sumatoria += current.consumo

    cantidad = len(consumo_list)
    promedio = sumatoria / cantidad / conversion_factor

    # frappe.errprint("cantidad %s" % cantidad)

    return promedio



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
    
    return order.as_dict()

@frappe.whitelist()
def validate_estimation_date(date):
    from constants import WEEK_DAY_SET
    
    day = frappe.db.get_single_value("Configuracion", "default_week_day", cache=False)
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
        amount = float(item.standard_rate) * float(detalle.order_sku_total)
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
        array.append(float(ZERO))

    return array[ZERO]
