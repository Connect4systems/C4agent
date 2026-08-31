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

SHIPMENT_WORKFLOW_STATES = (
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

SHIPMENT_WORKFLOW_ACTIONS = (
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

EXPENSE_WORKFLOW_STATES = ("Draft", "Pending Verification", "Approved", "Allocated", "Cancelled")
EXPENSE_WORKFLOW_ACTIONS = (
	"Submit for Verification",
	"Approve Expense",
	"Return to Draft",
	"Cancel Expense",
)

CUSTOMS_WORKFLOW_STATES = (
	"Draft", "Documents Submitted", "Under Review", "Under Inspection",
	"Duties Assessed", "Payment Pending", "Paid", "Released", "Cancelled",
)
CUSTOMS_WORKFLOW_ACTIONS = (
	"Submit Documents", "Start Review", "Start Inspection", "Assess Duties",
	"Request Payment", "Confirm Payment", "Release Shipment", "Cancel Declaration",
)

SINOSURE_WORKFLOW_STATES = ("Draft", "Pending Approval", "Approved", "Active", "Expired", "Closed", "Rejected")
SINOSURE_WORKFLOW_ACTIONS = ("Request Approval", "Approve", "Reject", "Activate", "Expire", "Close")

DEFAULT_IMPORT_EXPENSE_TYPES = (
	("Ocean Freight", 1, 0, "Amount"),
	("Customs Duty", 1, 0, "Amount"),
	("Import VAT", 0, 1, "Amount"),
	("Import Tax", 0, 0, "Amount"),
	("Customs Broker", 1, 0, "Amount"),
	("Port Charges", 1, 0, "Weight"),
	("Nafeza Fees", 1, 0, "Amount"),
	("Inspection", 1, 0, "Amount"),
	("Quarantine", 1, 0, "Amount"),
	("Storage", 1, 0, "Amount"),
	("Demurrage", 0, 0, "Amount"),
	("Detention", 0, 0, "Amount"),
	("Transportation", 1, 0, "Weight"),
	("Marine Insurance", 1, 0, "Amount"),
	("Bank Charges", 0, 0, "Amount"),
	("Sinosure Fee", 0, 0, "Amount"),
	("Documentation", 1, 0, "Amount"),
	("Other Import Expense", 0, 0, "Manual"),
)


def setup_c4agent():
	"""Install or update app-owned setup records idempotently."""
	setup_c4agent_roles()
	create_c4agent_custom_fields()
	setup_import_shipment_workflow()
	seed_import_expense_types()
	setup_import_expense_workflow()
	setup_customs_declaration_workflow()
	setup_sinosure_workflow()


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
				"fieldname": "custom_acid_issue_date",
				"fieldtype": "Date",
				"label": "ACID Issue Date",
				"insert_after": "custom_acid_number",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.acid_issue_date"
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
			{
				"fieldname": "custom_sinosure_coverage",
				"fieldtype": "Link",
				"label": "Sinosure Coverage",
				"options": "Sinosure Coverage",
				"insert_after": "custom_eta",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.sinosure_coverage"
			},
			{
				"fieldname": "custom_is_sinosure_covered",
				"fieldtype": "Check",
				"label": "Sinosure Covered",
				"insert_after": "custom_sinosure_coverage",
				"read_only": 1,
			},
			{
				"fieldname": "custom_sinosure_reference",
				"fieldtype": "Data",
				"label": "Sinosure Reference",
				"insert_after": "custom_is_sinosure_covered",
				"read_only": 1,
				"fetch_from": "custom_sinosure_coverage.sinosure_reference"
			},
			{
				"fieldname": "custom_import_containers",
				"fieldtype": "Table",
				"label": "Import Containers",
				"options": "Purchase Invoice Import Container",
				"insert_after": "custom_sinosure_reference",
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
		"Landed Cost Taxes and Charges": [
			{
				"fieldname": "custom_import_expense",
				"fieldtype": "Link",
				"label": "Import Expense",
				"options": "Import Expense",
				"insert_after": "description",
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

	ensure_workflow_masters(SHIPMENT_WORKFLOW_STATES, SHIPMENT_WORKFLOW_ACTIONS)

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
	for state in SHIPMENT_WORKFLOW_STATES[:-2]:
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


def seed_import_expense_types():
	"""Create editable policy defaults without overwriting finance changes."""
	if not frappe.db.exists("DocType", "Import Expense Type"):
		return

	for name, include_in_landed_cost, is_recoverable_tax, allocation_basis in (
		DEFAULT_IMPORT_EXPENSE_TYPES
	):
		if frappe.db.exists("Import Expense Type", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Import Expense Type",
				"expense_type_name": name,
				"include_in_landed_cost": include_in_landed_cost,
				"is_recoverable_tax": is_recoverable_tax,
				"allocation_basis": allocation_basis,
			}
		).insert(ignore_permissions=True)


def setup_import_expense_workflow():
	"""Create finance verification and approval workflow for Import Expense."""
	if not frappe.db.exists("DocType", "Import Expense"):
		return

	ensure_workflow_masters(EXPENSE_WORKFLOW_STATES, EXPENSE_WORKFLOW_ACTIONS)
	workflow_name = "Import Expense Approval"
	workflow = (
		frappe.get_doc("Workflow", workflow_name)
		if frappe.db.exists("Workflow", workflow_name)
		else frappe.new_doc("Workflow")
	)
	workflow.workflow_name = workflow_name
	workflow.document_type = "Import Expense"
	workflow.workflow_state_field = "expense_status"
	workflow.is_active = 1
	workflow.override_status = 0
	workflow.send_email_alert = 0
	workflow.set(
		"states",
		[
			{"state": "Draft", "doc_status": "0", "allow_edit": "Finance User"},
			{"state": "Pending Verification", "doc_status": "0", "allow_edit": "Finance User"},
			{"state": "Approved", "doc_status": "1", "allow_edit": "Finance Manager"},
			{"state": "Allocated", "doc_status": "1", "allow_edit": "Finance Manager"},
			{"state": "Cancelled", "doc_status": "2", "allow_edit": "Finance Manager"},
		],
	)
	transitions = (
		("Draft", "Submit for Verification", "Pending Verification", "Finance User"),
		("Draft", "Submit for Verification", "Pending Verification", "Finance Manager"),
		("Pending Verification", "Approve Expense", "Approved", "Finance Manager"),
		("Pending Verification", "Return to Draft", "Draft", "Finance Manager"),
		("Approved", "Cancel Expense", "Cancelled", "Finance Manager"),
	)
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


def setup_customs_declaration_workflow():
	if not frappe.db.exists("DocType", "Customs Declaration"):
		return
	ensure_workflow_masters(CUSTOMS_WORKFLOW_STATES, CUSTOMS_WORKFLOW_ACTIONS)
	workflow_name = "Customs Declaration Lifecycle"
	workflow = frappe.get_doc("Workflow", workflow_name) if frappe.db.exists("Workflow", workflow_name) else frappe.new_doc("Workflow")
	workflow.workflow_name = workflow_name
	workflow.document_type = "Customs Declaration"
	workflow.workflow_state_field = "clearance_status"
	workflow.is_active = 1
	workflow.override_status = 0
	workflow.send_email_alert = 0
	workflow.set("states", [
		{"state": state, "doc_status": "0", "allow_edit": "Customs Manager" if state in ("Paid", "Released", "Cancelled") else "Customs User"}
		for state in CUSTOMS_WORKFLOW_STATES
	])
	transitions = (
		("Draft", "Submit Documents", "Documents Submitted", "Customs User"),
		("Documents Submitted", "Start Review", "Under Review", "Customs User"),
		("Under Review", "Start Inspection", "Under Inspection", "Customs User"),
		("Under Review", "Assess Duties", "Duties Assessed", "Customs Manager"),
		("Under Inspection", "Assess Duties", "Duties Assessed", "Customs Manager"),
		("Duties Assessed", "Request Payment", "Payment Pending", "Customs Manager"),
		("Payment Pending", "Confirm Payment", "Paid", "Finance Manager"),
		("Paid", "Release Shipment", "Released", "Customs Manager"),
	)
	rows = [{"state": a, "action": b, "next_state": c, "allowed": d, "allow_self_approval": 1} for a, b, c, d in transitions]
	for state in CUSTOMS_WORKFLOW_STATES[:-2]:
		rows.append({"state": state, "action": "Cancel Declaration", "next_state": "Cancelled", "allowed": "Customs Manager", "allow_self_approval": 1})
	workflow.set("transitions", rows)
	workflow.insert(ignore_permissions=True) if workflow.is_new() else workflow.save(ignore_permissions=True)


def setup_sinosure_workflow():
	if not frappe.db.exists("DocType", "Sinosure Coverage"):
		return
	ensure_workflow_masters(SINOSURE_WORKFLOW_STATES, SINOSURE_WORKFLOW_ACTIONS)
	workflow_name = "Sinosure Coverage Lifecycle"
	workflow = frappe.get_doc("Workflow", workflow_name) if frappe.db.exists("Workflow", workflow_name) else frappe.new_doc("Workflow")
	workflow.workflow_name = workflow_name
	workflow.document_type = "Sinosure Coverage"
	workflow.workflow_state_field = "coverage_status"
	workflow.is_active = 1
	workflow.override_status = 0
	workflow.send_email_alert = 0
	workflow.set("states", [{"state": s, "doc_status": "0", "allow_edit": "Finance Manager"} for s in SINOSURE_WORKFLOW_STATES])
	transitions = (
		("Draft", "Request Approval", "Pending Approval"),
		("Pending Approval", "Approve", "Approved"),
		("Pending Approval", "Reject", "Rejected"),
		("Approved", "Activate", "Active"),
		("Active", "Expire", "Expired"),
		("Active", "Close", "Closed"),
	)
	workflow.set("transitions", [{"state": a, "action": b, "next_state": c, "allowed": "Finance Manager", "allow_self_approval": 1} for a, b, c in transitions])
	workflow.insert(ignore_permissions=True) if workflow.is_new() else workflow.save(ignore_permissions=True)


def ensure_workflow_masters(states, actions):
	"""Create shared Workflow State and Workflow Action Master records."""
	for state in states:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state}
			).insert(ignore_permissions=True)

	for action in actions:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc(
				{"doctype": "Workflow Action Master", "workflow_action_name": action}
			).insert(ignore_permissions=True)
