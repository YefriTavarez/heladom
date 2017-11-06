# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class MovimientodeInventario(Document):
    def on_submit(self):
        almacen_transito = frappe.get_value(
            "Warehouse", self.source_warehouse, "almacen_transito")
        if self.status == "En Almacen":
            carga(self.pedido, self.source_warehouse, almacen_transito)
            next_state(self.status, self.pedido)
        elif(self.status == "En Transito"):
            entrega(self.pedido, self.target_warehouse, almacen_transito)
            next_state(self.status, self.pedido)
        else:
            frappe.errprint("Status No Valido")


def carga(pedido, warehouse, almacen_transito):
    items = get_items(pedido, warehouse, almacen_transito)
    qsr = frappe.get_value("Warehouse", warehouse, "qsr")
    if(qsr == 1):
        almacen_ins = frappe.get_value("Warehouse", warehouse, "almacen_ins")
        material_transfer(items, warehouse, almacen_transito)
        salida_insumo(as_insumo(items), almacen_ins)
    else:
        material_transfer(items, warehouse, almacen_transito)


def entrega(pedido, warehouse, almacen_transito):
    items = get_items(pedido, almacen_transito, warehouse)
    qsr = frappe.get_value("Warehouse", warehouse, "qsr")
    if(qsr == 1):
        almacen_ins = frappe.get_value("Warehouse", warehouse, "almacen_ins")
        material_transfer(items, almacen_transito, warehouse)
        entrada_insumo(as_insumo(items), almacen_ins)
    else:
        material_transfer(items, almacen_transito, warehouse)


def salida_insumo(items, almacen_ins):
    material_issue = frappe.get_doc({
        "doctype": "Stock Entry",
        "naming_series": "STE-",
        "purpose": "Material Issue",
        "company": "Heladom",
        "from_warehouse": almacen_ins,
        "items": items
    })
    material_issue.insert()
    material_issue.save()
    material_issue.submit()


def entrada_insumo(items, almacen_ins):
    material_receipt = frappe.get_doc({
        "doctype": "Stock Entry",
        "naming_series": "STE-",
        "purpose": "Material Receipt",
        "company": "Heladom",
        "to_warehouse": almacen_ins,
        "items": items
    })
    material_receipt.insert()
    material_receipt.save()
    material_receipt.submit()


def as_insumo(items):
    items_insumo = []
    for item in items:
        insumo = frappe.get_value("Item", item["item_code"], [
                                  "insumo", "conversion_ins"])
        uom = frappe.get_value("Item", insumo[0], "stock_uom")
        qty = item["qty"] * insumo[1]
        items_insumo.append({
            "item_code": insumo[0],
            "qty": qty,
            "basic_rate": frappe.get_value("Stock Ledger Entry",
                                           {"item_code": item["item_code"]},
                                           "valuation_rate"),
            "uom": uom,
            "conversion_factor": 1,
            "stock_uom": uom,
            "transfer_qty": qty
        })
    return items_insumo


def get_items(pedido, s_warehouse, t_warehouse):
    items_pedido = frappe.get_doc("Material Request", pedido).items
    items = []
    for item in items_pedido:
        batch_no = frappe.get_value("Stock Ledger Entry", {
                                    "warehouse": s_warehouse,
                                    "item_code": item.item_code}, "batch_no")
        items.append({
            "item_code": item.item_code,
            "s_warehouse": s_warehouse,
            "t_warehouse": t_warehouse,
            "qty": item.qty,
            "uom": item.uom,
            "conversion_factor": 1,
            "stock_uom": item.uom,
            "transfer_qty": item.qty,
            "batch_no": batch_no
        })
    return items


def material_transfer(items, from_warehouse, to_warehouse):
    material_transfer = frappe.get_doc({
        "doctype": "Stock Entry",
        "naming_series": "STE-",
        "purpose": "Material Transfer",
        "company": "Heladom",
        "from_warehouse": from_warehouse,
        "to_warehouse": to_warehouse,
        "items": items
    })
    material_transfer.insert()
    material_transfer.save()
    material_transfer.submit()


def next_state(state, pedido):
    if(state == "En Almacen"):
        mr = frappe.get_doc("Material Request", pedido)
        mr.workflow_state = "En Transito"
        mr.save()
    elif(state == "En Transito"):
        mr = frappe.get_doc("Material Request", pedido)
        mr.workflow_state = "Entregado"
        mr.save()
        mr.submit()
    else:
        frappe.errprint("Status No Valido")
