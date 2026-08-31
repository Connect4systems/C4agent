# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe


def validate_import_shipment(doc, method=None):
	"""
	Validate Purchase Receipt has matching company and supplier with Import Shipment
	"""
	if not getattr(doc, "custom_import_shipment", None):
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
	if settings.require_customs_release_before_receipt and not frappe.db.exists(
		"Customs Declaration", {"import_shipment": doc.custom_import_shipment, "clearance_status": "Released"}
	):
		frappe.throw("A Released Customs Declaration is required before receiving this shipment")
	for item in doc.items:
		container_name = getattr(item, "custom_import_container", None)
		if settings.require_container_on_purchase_receipt_item and not container_name:
			frappe.throw(f"Row {item.idx}: Import Container is required")
		if not container_name:
			continue

		container_shipment = frappe.db.get_value(
			"Import Container", container_name, "import_shipment"
		)
		if not container_shipment:
			frappe.throw(f"Row {item.idx}: Import Container {container_name} does not exist")
		if container_shipment != doc.custom_import_shipment:
			frappe.throw(
				f"Row {item.idx}: Import Container {container_name} belongs to "
				f"shipment {container_shipment}, not {doc.custom_import_shipment}"
			)


def on_submit(doc, method=None):
	"""Update Import Shipment when Purchase Receipt is submitted"""
	if not getattr(doc, "custom_import_shipment", None):
		return

	refresh_shipment_receipt_summary(doc.custom_import_shipment)
	frappe.get_doc("Import Shipment", doc.custom_import_shipment).add_comment("Comment", f"Purchase Receipt {doc.name} submitted")


def on_cancel(doc, method=None):
	"""Update Import Shipment when Purchase Receipt is cancelled"""
	if not getattr(doc, "custom_import_shipment", None):
		return

	refresh_shipment_receipt_summary(
		doc.custom_import_shipment,
		exclude_receipt=doc.name,
	)


def refresh_shipment_receipt_summary(shipment_name, exclude_receipt=None):
	"""Refresh received quantities and value from submitted Purchase Receipts."""
	filters = {"custom_import_shipment": shipment_name, "docstatus": 1}
	if exclude_receipt:
		filters["name"] = ("!=", exclude_receipt)

	receipts = frappe.get_all("Purchase Receipt", filters=filters, fields=["name", "base_total"])
	receipt_names = [row.name for row in receipts]
	quantities_by_po_item = {}
	if receipt_names:
		items = frappe.get_all(
			"Purchase Receipt Item",
			filters={"parent": ("in", receipt_names)},
			fields=["purchase_order_item", "qty"],
		)
		for item in items:
			if item.purchase_order_item:
				quantities_by_po_item[item.purchase_order_item] = (
					quantities_by_po_item.get(item.purchase_order_item, 0) + (item.qty or 0)
				)

	shipment_items = frappe.get_all(
		"Import Shipment Item",
		filters={"parent": shipment_name},
		fields=["name", "purchase_order_item"],
	)
	for item in shipment_items:
		frappe.db.set_value(
			"Import Shipment Item",
			item.name,
			"received_qty",
			quantities_by_po_item.get(item.purchase_order_item, 0),
			update_modified=False,
		)

	frappe.db.set_value(
		"Import Shipment",
		shipment_name,
		"purchase_receipt_value",
		sum(row.base_total or 0 for row in receipts),
		update_modified=False,
	)
