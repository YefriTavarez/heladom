// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

var current_uoms, uoms_list, conversion_list;

frappe.ui.form.on("Toma de Inventario", {
  onload_post_render: function(frm) {
    if (frm.is_new()) {
      frm.set_value("item_table", []);
    }
  },
  set_cantidad: function(frm) {
    frappe.prompt(
      [
        {
          fieldname: "cantidad",
          fieldtype: "Float",
          label: "Cantidad",
          reqd: 1
        }
      ],
      function(values) {
        // if (values.cantidad * frm.doc.conversion_factor > 1) {
        //   frappe.msgprint("Cantidad invalida", "Error");
        //   frm.trigger("set_cantidad");
        // } else {
          frm.doc.cantidad = values.cantidad;
          frm.trigger("validate_item");
        // }
      },
      "Cantidad",
      "Ok"
    );
  },
  set_unidad: function(frm) {
    uoms_list = [];
    conversion_list = [];
    $.each(current_uoms, function(index, value) {
      uoms_list.push(value.uom);
      conversion_list.push(value.conversion_factor);
    });
    frappe.prompt(
      [
        {
          fieldname: "uom",
          fieldtype: "Select",
          label: "Unidad",
          options: [" "].concat(uoms_list),
          reqd: 1
        }
      ],
      function(values) {
        var index = uoms_list.indexOf(values.uom);
        frm.set_value("uom", values.uom);
        frm.doc.conversion_factor = conversion_list[index];
        frm.trigger("validate_uom");
      },
      "Elige la Unidad de Medida",
      "Ok"
    );
  },
  validate_uom: function(frm) {
    frappe.call({
      method: "frappe.client.get_value",
      args: {
        doctype: "UOM",
        filters: {
          uom_name: frm.doc.uom
        },
        fieldname: ["directo"]
      },
      callback: function(r) {
        if (r.message.directo === 1) {
          frm.doc.cantidad = 1;
          frm.trigger("validate_item");
        } else {
          frm.trigger("set_cantidad");
        }
      }
    });
  },

  validate_item: function(frm) {
    var cantidad = flt(frm.doc.cantidad) * flt(frm.doc.conversion_factor);
    for (var i = 0; i < frm.doc.item_table.length; i++) {
      if (frm.doc.item_table[i].item === frm.doc.item) {
        cantidad += frm.doc.item_table[i].cantidad;
        frm.doc.show_qty = cantidad;
      }
    }
    frappe.call({
      method:
        "heladom.heladom.doctype.toma_de_inventario.toma_de_inventario.validate_item",
      args: {
        item_code: frm.doc.item,
        warehouse: frm.doc.almacen
      },
      callback: function(r) {
        if (r.message.cantidad_en_stock <= 0) {
          frappe.msgprint("Item no existe en almacen", "Error");
          frm.set_value("barcode", null);
        } else if (
          r.message.cantidad_en_stock[0].qty_after_transaction < cantidad
        ) {
          frappe.msgprint("Excede existencia en Almacen", "Error");
          frm.set_value("barcode", null);
        } else if (r.message.tipo_y_insumo[0] !== "SKU") {
          frappe.msgprint("Item no es SKU", "Error");
          frm.set_value("barcode", null);
        } else if (!r.message.tipo_y_insumo[1]) {
          frappe.msgprint("Item no tiene Insumo Definido", "Error");
          frm.set_value("barcode", null);
        } else if (r.message.insumo_diario === 0) {
          frappe.msgprint("Item no es Insumo Diario", "Error");
          frm.set_value("barcode", null);
        } else {
          frm.trigger("add_toma");
        }
      }
    });
  },

  set_tipo_toma: function(frm) {
    var d = new Date();
    if (d.getDay() === 1) {
      frm.set_value("tipo_toma", "Inventario Fisico");
    } else {
      frm.set_value("tipo_toma", "Inventario Diario");
    }
  },

  tipo_almacen: function(frm) {
    if (frm.doc.tipo_almacen === "Standard") {
      frm.set_value("tipo_toma", "Inventario Fisico");
    } else {
      frm.trigger("set_tipo_toma");
    }
    frm.trigger("set_almacenes");
  },

  set_almacenes: function(frm) {
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Warehouse",
        filters: {
          parent_warehouse:
            frm.doc.tipo_almacen === "Standard" ? "Almacen - H" : "QSR - H"
        },
        fieldname: ["warehouse_name"]
      },
      callback: function(r) {
        frm.set_df_property(
          "almacen",
          "options",
          (function() {
            var array = [" "];
            for (var i = 0; i < r.message.length; i++) {
              array.push(r.message[i].name);
            }
            return array;
          })()
        );
        frm.refresh_field("almacen");
      }
    });
  },

  almacen: function(frm) {
    frm.set_df_property("almacen", "read_only", 1);
    frm.set_df_property("tipo_almacen", "read_only", 1);
    frm.refresh_field("almacen");
    frm.refresh_field("tipo_almacen");
  },

  add_toma: function(frm) {
    var i,
      control = false;
    $.each(frm.doc.item_table, function(index, value) {
      if (value.item === frm.doc.item && value.area === frm.doc.area) {
        control = true;
        i = index;
      }
    });
    if (control) {
      // var request = {
      //     "method": "heladom.api.get_stock_balance"
      // }

      // request.args = {
      // 	"warehouse": frm.doc.almacen,
      // 	"item_code": frm.doc.item_table[i].item
      // }

      // request.callback = function(response) {
      // 	var balance = response.message

      // 	if (balance) {
      // 		if (flt(frm.doc.item_table[i].cantidad) < flt(balance)) {
      frm.doc.item_table[i].cantidad +=
        flt(frm.doc.cantidad) * flt(frm.doc.conversion_factor);
      refresh_field("item_table");
      // 		}
      // 	}
      // }

      // frappe.call(request)
    } else {
      frm.add_child("item_table", {
        item: frm.doc.item,
        nombre_item: frm.doc.item_name,
        area: frm.doc.area,
        unidad: frm.doc.stock_uom,
        cantidad: frm.doc.cantidad * parseFloat(frm.doc.conversion_factor),
        almacen: frm.doc.almacen
      });
    }
    frm.set_value("last_item", frm.doc.item_name);
    frm.set_value("last_uom", frm.doc.uom);
    frm.set_value("last_cantidad", frm.doc.show_qty || frm.doc.cantidad);
    frm.set_value("barcode", null);
    frm.refresh_field("item_table");
  },

  cambiar_unidad: function(frm) {
    frappe.prompt(
      [
        {
          fieldname: "uom",
          fieldtype: "Select",
          label: "Unidad",
          options: [" "].concat(uoms_list),
          reqd: 1
        }
      ],
      function(values) {
        var index = uoms_list.indexOf(values.uom);
        frm.set_value("uom", values.uom);
        frm.doc.conversion_factor = conversion_list[index];
      },
      "Elige la Unidad de Medida",
      "Ok"
    );
  },

  barcode: function(frm) {
    if (frm.doc.barcode) {
      if (frm.doc.barcode.indexOf(" ") > -1) {
        var index = frm.doc.barcode.indexOf(" ") - 1;
        frm.doc.barcode = frm.doc.barcode.substr(2, index);
      }
      frappe.call({
        method:
          "heladom.heladom.doctype.toma_de_inventario.toma_de_inventario.get_item",
        args: {
          barcode: frm.doc.barcode
        },
        callback: function(r) {
          if (r.message) {
            if (r.message.grupo_de_conteo === frm.doc.grupo_de_conteo) {
              frm.doc.item = r.message.item_code;
              frm.doc.item_name = r.message.item_name;
              frm.trigger("validate_uom");
            } else {
              frm.doc.grupo_de_conteo = r.message.grupo_de_conteo;
              frm.doc.item = r.message.item_code;
              frm.doc.item_name = r.message.item_name;
              frm.doc.stock_uom = r.message.stock_uom;
              current_uoms = r.message.uoms;
              frm.trigger("set_unidad");
            }
          } else {
            frappe.msgprint("Codigo de Barra Invalido", "Error");
            frm.set_value("barcode", null);
          }
        }
      });
      // cleanup the barcode field asap, so that the user can trigger another push
      // while the system is waiting for the server
      frm.set_value('barcode', ""); 
    }
  }
});
