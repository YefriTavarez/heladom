frappe.listview_settings["Pedido en Linea"] = {
	onload: function(page) {
		var required_role = "Administrador de Pedidos"
		if (frappe.user.has_role(required_role)) {
			frappe.provide("hm.interval")
			hm.interval.refresh_pedido = setInterval(function() {
				var route = frappe.get_route()

				if (route.length == 2 && route[0] == "List" && route[1] == "Pedido en Linea") {

					page.refresh()
				} else {
					clearInterval(hm.interval.refresh_pedido)
				}
			}, 10000)
		}
	}
}