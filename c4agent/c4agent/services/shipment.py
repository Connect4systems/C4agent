# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime


def make_import_shipment(source_name, target_doc=None):
	"""
	Create Import Shipment from Purchase Order
	Used for button "Create > Import Shipment" on Purchase Order
	"""
	
	if not frappe.db.exists("Purchase Order", source_name):
		frappe.throw(f"Purchase Order {source_name} does not exist")
	
	po = frappe.get_doc("Purchase Order", source_name)
	
	if po.docstatus != 1:
		frappe.throw("Purchase Order must be submitted before creating Import Shipment")
	
	# Create new Import Shipment
	if not target_doc:
		target_doc = frappe.new_doc("Import Shipment")
	
	target_doc.company = po.company
	target_doc.supplier = po.supplier
	target_doc.purchase_order = po.name
	
	# Get supplier currency from PO
	if po.currency:
		target_doc.supplier_currency = po.currency
	
	# Auto-add items from PO
	target_doc.items = []
	for po_item in po.items:
		target_doc.append("items", {
			"purchase_order_item": po_item.name,
			"item_code": po_item.item_code,
			"item_name": po_item.item_name,
			"uom": po_item.uom,
			"ordered_qty": po_item.qty,
			"shipped_qty": 0,
			"rate": po_item.rate,
		})
	
	return target_doc


@frappe.whitelist()
def create_import_shipment_from_po(po_name):
	"""
	Whitelisted method to create Import Shipment from PO button
	"""
	try:
		shipment_doc = make_import_shipment(po_name)
		shipment_doc.insert()
		frappe.msgprint(
			f"Import Shipment {shipment_doc.name} created successfully",
			alert=True
		)
		return shipment_doc.name
	except Exception as e:
		frappe.throw(str(e))
