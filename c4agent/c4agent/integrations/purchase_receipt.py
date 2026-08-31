# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe


def validate_import_shipment(doc, method=None):
	"""
	Validate Purchase Receipt has matching company and supplier with Import Shipment
	"""
	if not doc.custom_import_shipment:
		return
	
	shipment = frappe.get_doc("Import Shipment", doc.custom_import_shipment)
	
	# Validate company match
	if doc.company != shipment.company:
		frappe.throw(
			f"Purchase Receipt company '{doc.company}' does not match "
			f"Import Shipment company '{shipment.company}'"
		)
	
	# Validate supplier match
	if doc.supplier != shipment.supplier:
		frappe.throw(
			f"Purchase Receipt supplier '{doc.supplier}' does not match "
			f"Import Shipment supplier '{shipment.supplier}'"
		)
	
	# Validate container references
	settings = frappe.get_single("C4agent Settings")
	if settings.require_container_on_purchase_receipt_item:
		for item in doc.items:
			if doc.custom_import_shipment and not item.custom_import_container:
				frappe.msgprint(
					f"Row {item.idx}: Container should be specified for Purchase Receipt Item",
					alert=True
				)


def on_submit(doc, method=None):
	"""Update Import Shipment when Purchase Receipt is submitted"""
	if not doc.custom_import_shipment:
		return
	
	shipment = frappe.get_doc("Import Shipment", doc.custom_import_shipment)
	shipment.refresh_summary_totals()
	shipment.save()


def on_cancel(doc, method=None):
	"""Update Import Shipment when Purchase Receipt is cancelled"""
	if not doc.custom_import_shipment:
		return
	
	shipment = frappe.get_doc("Import Shipment", doc.custom_import_shipment)
	shipment.refresh_summary_totals()
	shipment.save()
