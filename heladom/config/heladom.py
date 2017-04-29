# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Docs"),
			"items": [
				{
					"type": "doctype",
					"name": "Estimacion de Compras",
					#"description": _(""),
				},
				{
					"type": "doctype",
					"label": "Orden de Compra",
					"name": "Purchase Order",
					#"description": _("Groups of DocTypes"),
				},
				{
					"type": "doctype",
					"name": "Detalle de Estimacion",
					#"description": _("Groups of DocTypes"),
				},
				{
					"type": "doctype",
					"name": "Administrador de Pedidos",
					#"description": _("Pages in Desk (place holders)"),
				},
				{
					"type": "doctype",
					"name": "Factura Internacional",
					#"description": _("Script or Query reports"),
				},
				{
					"type": "doctype",
					"name": "Inventario Fisico Helados",
				#	"description": _("Customized Formats for Printing, Email"),
				},
				{
					"type": "doctype",
					"name": "Inventario Helado",
					#"description": _("Client side script extensions in Javascript"),
				}
			]
		}
	]