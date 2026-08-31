# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe


def validate_import_shipment(doc, method=None):
	"""
	Validate Purchase Invoice has matching company and supplier with Import Shipment
	"""
	if not doc.custom_import_shipment:
		return
	
	shipment = frappe.get_doc("Import Shipment", doc.custom_import_shipment)
	
	# Validate company match
	if doc.company != shipment.company:
		frappe.throw(
			f"Purchase Invoice company '{doc.company}' does not match "
			f"Import Shipment company '{shipment.company}'"
		)
	
	# Validate supplier match
	if doc.supplier != shipment.supplier:
		frappe.throw(
			f"Purchase Invoice supplier '{doc.supplier}' does not match "
			f"Import Shipment supplier '{shipment.supplier}'"
		)
