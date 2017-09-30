import frappe

def cost_center_admins(doctype, txt, searchfield, start, page_len, filters):
	role_list = frappe.get_list("UserRole", {
		"role": "Gerente de Tienda", 
		"parent": ["!=", "Administrator"]
	}, ["parent"])

	return [[role.parent] for role in role_list]

