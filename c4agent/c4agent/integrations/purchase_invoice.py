# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe


def validate_import_shipment(doc, method=None):
	"""
	Validate Purchase Invoice has matching company and supplier with Import Shipment
	"""
	is_foreign = frappe.db.get_value("Supplier", doc.supplier, "custom_is_foreign_supplier")
	if is_foreign and not getattr(doc, "custom_import_shipment", None):
		frappe.throw("Import Shipment is required for a foreign supplier Purchase Invoice")
	if not getattr(doc, "custom_import_shipment", None):
		return
	
	shipment = frappe.get_doc("Import Shipment", doc.custom_import_shipment)
	doc.custom_is_sinosure_covered = 1 if shipment.sinosure_coverage else 0
	
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

	missing = [label for field, label in (
		("acid_number", "ACID Number"),
		("acid_issue_date", "ACID Issue Date"),
		("shipping_line", "Shipping Line"),
	) if not shipment.get(field)]
	if is_foreign and missing:
		frappe.throw("Complete the linked Import Shipment before invoicing: " + ", ".join(missing))

	for row in doc.items:
		if row.purchase_order and row.purchase_order != shipment.purchase_order:
			frappe.throw(f"Row {row.idx}: Purchase Order does not belong to the linked Import Shipment")

	seen = set()
	for row in getattr(doc, "custom_import_containers", []):
		if row.import_container in seen:
			frappe.throw(f"Import Container {row.import_container} is listed more than once")
		seen.add(row.import_container)
		container_shipment = frappe.db.get_value("Import Container", row.import_container, "import_shipment")
		if container_shipment != shipment.name:
			frappe.throw(f"Import Container {row.import_container} does not belong to shipment {shipment.name}")
