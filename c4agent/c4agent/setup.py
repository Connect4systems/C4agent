# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


ROLES = (
	"Import User",
	"Import Manager",
	"Customs User",
	"Customs Manager",
	"Finance User",
	"Finance Manager",
)

WORKFLOW_STATES = (
	"Draft",
	"Ordered",
	"Booked",
	"In Transit",
	"Arrived",
	"Under Customs Clearance",
	"Cleared",
	"Received",
	"Closed",
	"Cancelled",
)

WORKFLOW_ACTIONS = (
	"Confirm Order",
	"Confirm Booking",
	"Confirm Departure",
	"Confirm Arrival",
	"Start Customs",
	"Confirm Customs Release",
	"Confirm Receipt",
	"Close Shipment",
	"Cancel Shipment",
)


def setup_c4agent():
	"""Install or update app-owned setup records idempotently."""
	setup_c4agent_roles()
	create_c4agent_custom_fields()
	setup_import_shipment_workflow()


def create_c4agent_custom_fields():
	"""Create custom fields on standard doctypes"""
	
	custom_fields = {
		"Supplier": [
			{
				"fieldname": "custom_is_foreign_supplier",
				"fieldtype": "Check",
				"label": "Is Foreign Supplier",
				"insert_after": "supplier_type"
			},
			{
				"fieldname": "custom_is_shipping_agent",
				"fieldtype": "Check",
				"label": "Is Shipping Agent",
				"insert_after": "custom_is_foreign_supplier"
			},
			{
				"fieldname": "custom_is_customs_broker",
				"fieldtype": "Check",
				"label": "Is Customs Broker",
				"insert_after": "custom_is_shipping_agent"
			},
			{
				"fieldname": "custom_is_logistics_provider",
				"fieldtype": "Check",
				"label": "Is Logistics Provider",
				"insert_after": "custom_is_customs_broker"
			},
		],
		"Purchase Invoice": [
			{
				"fieldname": "custom_import_info_section",
				"fieldtype": "Section Break",
				"label": "Import Information",
				"insert_after": "remarks"
			},
			{
				"fieldname": "custom_import_shipment",
				"fieldtype": "Link",
				"label": "Import Shipment",
				"options": "Import Shipment",
				"insert_after": "custom_import_info_section"
			},
			{
				"fieldname": "custom_acid_number",
				"fieldtype": "Data",
				"label": "ACID Number",
				"insert_after": "custom_import_shipment",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.acid_number"
			},
			{
				"fieldname": "custom_bill_of_lading",
				"fieldtype": "Data",
				"label": "Bill of Lading",
				"insert_after": "custom_acid_number",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.bill_of_lading"
			},
			{
				"fieldname": "custom_shipping_line",
				"fieldtype": "Link",
				"label": "Shipping Line",
				"options": "Shipping Line",
				"insert_after": "custom_bill_of_lading",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.shipping_line"
			},
			{
				"fieldname": "custom_vessel",
				"fieldtype": "Data",
				"label": "Vessel",
				"insert_after": "custom_shipping_line",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.vessel"
			},
			{
				"fieldname": "custom_voyage",
				"fieldtype": "Data",
				"label": "Voyage",
				"insert_after": "custom_vessel",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.voyage"
			},
			{
				"fieldname": "custom_etd",
				"fieldtype": "Date",
				"label": "ETD",
				"insert_after": "custom_voyage",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.etd"
			},
			{
				"fieldname": "custom_eta",
				"fieldtype": "Date",
				"label": "ETA",
				"insert_after": "custom_etd",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.eta"
			},
		],
		"Purchase Receipt": [
			{
				"fieldname": "custom_import_shipment",
				"fieldtype": "Link",
				"label": "Import Shipment",
				"options": "Import Shipment",
				"insert_after": "remarks"
			},
		],
		"Purchase Receipt Item": [
			{
				"fieldname": "custom_import_container",
				"fieldtype": "Link",
				"label": "Import Container",
				"options": "Import Container",
				"insert_after": "price_list_rate"
			},
		],
		"Landed Cost Voucher": [
			{
				"fieldname": "custom_import_shipment",
				"fieldtype": "Link",
				"label": "Import Shipment",
				"options": "Import Shipment",
				"insert_after": "remarks"
			},
		],
		"Item": [
			{
				"fieldname": "custom_wattage",
				"fieldtype": "Float",
				"label": "Wattage (for Solar Panels)",
				"precision": 2,
				"insert_after": "weight_uom"
			},
		],
	}
	
	create_custom_fields(custom_fields, ignore_validate=True)


def setup_c4agent_roles():
	"""Create roles for C4agent"""
	for role_name in ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def setup_import_shipment_workflow():
	"""Create the operational shipment workflow used by the read-only status field."""
	if not frappe.db.exists("DocType", "Import Shipment"):
		return

	for state in WORKFLOW_STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state}
			).insert(ignore_permissions=True)

	for action in WORKFLOW_ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)

	workflow_name = "Import Shipment Lifecycle"
	workflow = (
		frappe.get_doc("Workflow", workflow_name)
		if frappe.db.exists("Workflow", workflow_name)
		else frappe.new_doc("Workflow")
	)
	workflow.workflow_name = workflow_name
	workflow.document_type = "Import Shipment"
	workflow.workflow_state_field = "shipment_status"
	workflow.is_active = 1
	workflow.override_status = 0
	workflow.send_email_alert = 0

	workflow.set(
		"states",
		[
			{"state": "Draft", "doc_status": "0", "allow_edit": "Import User"},
			{"state": "Ordered", "doc_status": "0", "allow_edit": "Import User"},
			{"state": "Booked", "doc_status": "0", "allow_edit": "Import User"},
			{"state": "In Transit", "doc_status": "0", "allow_edit": "Import User"},
			{"state": "Arrived", "doc_status": "0", "allow_edit": "Import User"},
			{"state": "Under Customs Clearance", "doc_status": "0", "allow_edit": "Import User"},
			{"state": "Cleared", "doc_status": "0", "allow_edit": "Import Manager"},
			{"state": "Received", "doc_status": "0", "allow_edit": "Import Manager"},
			{"state": "Closed", "doc_status": "0", "allow_edit": "Import Manager"},
			{"state": "Cancelled", "doc_status": "0", "allow_edit": "Import Manager"},
		],
	)

	transitions = [
		("Draft", "Confirm Order", "Ordered", "Import Manager"),
		("Ordered", "Confirm Booking", "Booked", "Import User"),
		("Ordered", "Confirm Booking", "Booked", "Import Manager"),
		("Booked", "Confirm Departure", "In Transit", "Import User"),
		("Booked", "Confirm Departure", "In Transit", "Import Manager"),
		("In Transit", "Confirm Arrival", "Arrived", "Import User"),
		("In Transit", "Confirm Arrival", "Arrived", "Import Manager"),
		("Arrived", "Start Customs", "Under Customs Clearance", "Import Manager"),
		("Arrived", "Start Customs", "Under Customs Clearance", "Customs User"),
		("Under Customs Clearance", "Confirm Customs Release", "Cleared", "Customs Manager"),
		("Cleared", "Confirm Receipt", "Received", "Import Manager"),
		("Received", "Close Shipment", "Closed", "Import Manager"),
		("Received", "Close Shipment", "Closed", "Finance Manager"),
	]
	for state in WORKFLOW_STATES[:-2]:
		transitions.append((state, "Cancel Shipment", "Cancelled", "Import Manager"))

	workflow.set(
		"transitions",
		[
			{
				"state": state,
				"action": action,
				"next_state": next_state,
				"allowed": role,
				"allow_self_approval": 1,
			}
			for state, action, next_state, role in transitions
		],
	)

	if workflow.is_new():
		workflow.insert(ignore_permissions=True)
	else:
		workflow.save(ignore_permissions=True)
