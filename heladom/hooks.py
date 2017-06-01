# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "heladom"
app_title = "Heladom"
app_publisher = "Soldeva SRL"
app_description = "Aplicacion para el manejo de la compañia Heladom"
app_icon = "octicon octicon-package"
app_color = "#e27eb1"
app_email = "servicio@soldeva.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/heladom/css/heladom.css"
# app_include_js = "/assets/heladom/js/heladom.js"

# include js, css files in header of web template
# web_include_css = "/assets/heladom/css/heladom.css"
# web_include_js = "/assets/heladom/js/heladom.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "heladom.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "heladom.install.before_install"
# after_install = "heladom.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "heladom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"heladom.tasks.all"
# 	],
# 	"daily": [
# 		"heladom.tasks.daily"
# 	],
# 	"hourly": [
# 		"heladom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"heladom.tasks.weekly"
# 	]
# 	"monthly": [
# 		"heladom.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "heladom.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "heladom.event.get_events"
# }

