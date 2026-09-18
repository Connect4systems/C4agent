# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.workflow import apply_workflow


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
					"set_warehouse": "final_destination",
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


@frappe.whitelist()
def confirm_booking(shipment, shipping_line, bill_of_lading, port_of_loading, port_of_discharge, etd, eta):
	"""Save booking details and transition an ordered shipment to Booked."""
	doc = frappe.get_doc("Import Shipment", shipment)
	doc.check_permission("write")
	if doc.shipment_status != "Ordered":
		frappe.throw("Only an Ordered shipment can be confirmed as booked")
	if not all((shipping_line, bill_of_lading, port_of_loading, port_of_discharge, etd, eta)):
		frappe.throw("Shipping Line, Bill of Lading, ports, ETD, and ETA are required")
	if eta < etd:
		frappe.throw("ETA cannot be before ETD")
	doc.update({
		"shipping_line": shipping_line,
		"bill_of_lading": bill_of_lading,
		"port_of_loading": port_of_loading,
		"port_of_discharge": port_of_discharge,
		"etd": etd,
		"eta": eta,
	})
	doc.save()
	return apply_workflow(doc, "Confirm Booking")


@frappe.whitelist()
def confirm_departure(shipment, acid_number, actual_departure_date):
	"""Save departure details and transition a booked shipment to In Transit."""
	doc = frappe.get_doc("Import Shipment", shipment)
	doc.check_permission("write")
	if doc.shipment_status != "Booked":
		frappe.throw("Only a Booked shipment can have its departure confirmed")
	if not all((acid_number, actual_departure_date)):
		frappe.throw("ACID Number and Actual Departure Date are required")
	doc.acid_number = acid_number
	doc.actual_departure_date = actual_departure_date
	doc.save()
	return apply_workflow(doc, "Confirm Departure")


@frappe.whitelist()
def confirm_arrival(shipment, actual_arrival_date):
	"""Save the actual arrival date and transition an in-transit shipment to Arrived."""
	doc = frappe.get_doc("Import Shipment", shipment)
	doc.check_permission("write")
	if doc.shipment_status != "In Transit":
		frappe.throw("Only an In Transit shipment can have its arrival confirmed")
	if not actual_arrival_date:
		frappe.throw("Actual Arrival Date is required")
	doc.actual_arrival_date = actual_arrival_date
	doc.save()
	return apply_workflow(doc, "Confirm Arrival")


@frappe.whitelist()
def close_import_shipment(shipment, override_reason=None):
	doc = frappe.get_doc("Import Shipment", shipment)
	if not ({"Import Manager", "Finance Manager", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Only an Import Manager or Finance Manager can close a shipment", frappe.PermissionError)
	if doc.shipment_status != "Received":
		frappe.throw("Only a Received shipment can be closed")
	if override_reason is not None:
		doc.close_override_reason = override_reason
	doc.shipment_status = "Closed"
	doc.save()
	if override_reason:
		doc.add_comment("Comment", f"Shipment closed with override: {override_reason}")
	return doc.name


@frappe.whitelist()
def reopen_import_shipment(shipment, reason):
	if not reason:
		frappe.throw("Reopen Reason is required")
	if not ({"Import Manager", "Finance Manager", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Only an Import Manager, Finance Manager, or System Manager can reopen a shipment", frappe.PermissionError)
	doc = frappe.get_doc("Import Shipment", shipment)
	if doc.shipment_status != "Closed":
		frappe.throw("Only a Closed shipment can be reopened")
	frappe.db.set_value("Import Shipment", doc.name, {
		"shipment_status": "Received", "reopen_reason": reason,
		"closed_on": None, "closed_by": None,
	})
	doc.add_comment("Comment", f"Shipment reopened by {frappe.session.user}: {reason}")
	return doc.name
