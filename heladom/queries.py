import frappe

def cost_center_admins(doctype, txt, searchfield, start, page_len, filters):
	role_list = frappe.get_list("UserRole", {
		"role": "Gerente de Tienda", 
		"parent": ["!=", "Administrator"]
	}, ["parent"])

	return [[role.parent] for role in role_list]

def uom_item_query(doctype, txt, searchfield, start, page_len, filters):
	uom_list = frappe.get_list("UOM Conversion Detail", { 
		"parent": filters.get("item"),
		"uom": ["like", "%{}%".format(txt) if txt else "%"]
		}, ["uom"], order_by="uom")

	return [[row.uom] for row in uom_list]
