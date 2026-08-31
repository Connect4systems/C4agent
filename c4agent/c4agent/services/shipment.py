# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_import_shipment(source_name, target_doc=None):
	"""
	Create Import Shipment from Purchase Order
	Used for button "Create > Import Shipment" on Purchase Order
	"""
	
	if not frappe.db.exists("Purchase Order", source_name):
		frappe.throw(f"Purchase Order {source_name} does not exist")
	
	po = frappe.get_doc("Purchase Order", source_name)
	if not frappe.has_permission("Purchase Order", "read", doc=po):
		frappe.throw("Not permitted to read this Purchase Order", frappe.PermissionError)
	if not frappe.has_permission("Import Shipment", "create"):
		frappe.throw("Not permitted to create an Import Shipment", frappe.PermissionError)
	
	if po.docstatus != 1:
		frappe.throw("Purchase Order must be submitted before creating Import Shipment")
	
	def set_item_values(source, target, source_parent):
		wattage = frappe.db.get_value("Item", source.item_code, "custom_wattage") or 0
		target.shipped_qty = 0
		target.wattage = wattage
		target.total_watts = (target.ordered_qty or 0) * wattage

	return get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Import Shipment",
				"field_map": {
					"name": "purchase_order",
					"currency": "supplier_currency",
				},
			},
			"Purchase Order Item": {
				"doctype": "Import Shipment Item",
				"field_map": {
					"name": "purchase_order_item",
					"qty": "ordered_qty",
				},
				"postprocess": set_item_values,
			},
		},
		target_doc,
	)


@frappe.whitelist()
def create_import_shipment_from_po(po_name):
	"""
	Backward-compatible API returning an unsaved Import Shipment.
	"""
	return make_import_shipment(po_name)
