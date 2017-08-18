# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe

# Global constants

ZERO = 0
DRAFT = ZERO
SUBMITTED = 1
CANCELLED = 2
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6
SUNDAY = 7
WEEK_DAYS = 7
ONE_YEAR = 1
WEEKS_IN_YEAR = 52

WEEK_DAY_SET = [
	frappe._dict({"value": "1", "label": "Lunes"}),
	frappe._dict({"value": "2", "label": "Martes"}),
	frappe._dict({"value": "3", "label": "Miercoles"}),
	frappe._dict({"value": "4", "label": "Jueves"}),
	frappe._dict({"value": "5", "label": "Viernes"}),
	frappe._dict({"value": "6", "label": "Sabado"}),
	frappe._dict({"value": "7", "label": "Domingo"})
]
