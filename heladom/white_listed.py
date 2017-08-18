# -*- coding: utf-8 -*-
# Copyright (c) 2015, Soldeva, SRL and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def get_list(doctype):
    doclist = frappe.db.sql("""SELECT name 
        FROM `tab{0}`
        WHERE docstatus <> 2 ORDER BY name ASC""".format(doctype),
        as_dict=True)

    return doclist or []

def get_script(doctype):
    return """frappe.ui.form.on("%(doctype)s", "refresh", function(frm){
    var callback = function(response){
        if(frm.doc.__islocal || !response.message) return 

        var list = response.message
        var index = 0, prev_index = 0, next_index = 0
        var cur_route, prev_route, next_route

        for( ; index < list.length; index ++){
            prev_index = index - 1 < 0 ? 0 : index - 1
            next_index = index + 1 >= list.length ? list.length - 1 : index + 1

            if(frm.doc.name == list[index].name){
                prev_route = list[prev_index].name
                next_route = list[next_index].name
                cur_route = list[index].name

                break
            }
        }

        if(prev_route != cur_route) frm.add_custom_button("<< Prev",  function(e){ 
            frappe.set_route(["Form", frm.doc.doctype, prev_route]) 
        })

        if(next_route != cur_route) frm.add_custom_button("Next >>", function(e){ 
            frappe.set_route(["Form", frm.doc.doctype, next_route]) 
        })
    }

    frappe.call({
        method : "frappe.client.get_list",
        args : { 
            "doctype": frm.doctype, 
            "docname": frm.docname
        },
        callback : callback
    })
})"""% {"doctype": doctype}

def setup_navigation_buttons():
    for doctype in frappe.get_list("DocType", fields=["name", "istable", "issingle", "document_type"]):
        if doctype.istable or doctype.issingle or not doctype.document_type == "Document":
            continue

        try:
            doc = frappe.get_doc("Custom Script", "{0}-Client".format(doctype.name))
            #to start in a new line
            doc.script += """
//Apending Custom Script for the navigation buttons
""" + get_script(doctype.name)
            doc.save()
            print "Apending script to existing Custom Script for doctype {0}".format(doctype.name)
        except Exception:
            print "Adding new Custom Script to doctype {0}".format(doctype.name)

            cs = frappe.get_doc({
                "doctype" : "Custom Script",
                "dt" : doctype.name,
                "script_type" : "Client",
                "script" : get_script(doctype.name)
            })
            
            cs.insert()


@frappe.whitelist()
def money_in_words(number, main_currency=None, fraction_currency=None):
    return frappe.utils.money_in_words(number, main_currency, fraction_currency)

@frappe.whitelist()
def get_week_day_set():
    from constants import WEEK_DAY_SET

    return WEEK_DAY_SET