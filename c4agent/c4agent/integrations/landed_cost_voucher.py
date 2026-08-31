# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe


def validate_import_shipment(doc, method=None):
	"""
	Validate Landed Cost Voucher has matching Import Shipment
	"""
	if not doc.custom_import_shipment:
		return
	
	if not frappe.db.exists("Import Shipment", doc.custom_import_shipment):
		frappe.throw(f"Import Shipment {doc.custom_import_shipment} does not exist")


def on_submit(doc, method=None):
	"""
	Mark Import Expenses as allocated when LCV is submitted
	"""
	if not doc.custom_import_shipment:
		return
	
	# Get all Import Expenses linked to this shipment and included in LCV
	# This is a simplified version - would need actual LCV line item mapping
	expenses = frappe.get_all(
		"Import Expense",
		filters={
			"import_shipment": doc.custom_import_shipment,
			"include_in_landed_cost": 1,
			"landed_cost_allocated": 0,
			"docstatus": 1
		},
		fields=["name"]
	)
	
	# Mark them as allocated
	for expense in expenses:
		exp_doc = frappe.get_doc("Import Expense", expense.name)
		exp_doc.landed_cost_allocated = 1
		exp_doc.landed_cost_voucher = doc.name
		exp_doc.save()
	
	frappe.db.commit()


def on_cancel(doc, method=None):
	"""
	Reset Import Expense allocation when LCV is cancelled
	"""
	if not doc.custom_import_shipment:
		return
	
	# Find all expenses allocated to this LCV and reset them
	expenses = frappe.get_all(
		"Import Expense",
		filters={
			"landed_cost_voucher": doc.name,
		},
		fields=["name"]
	)
	
	for expense in expenses:
		exp_doc = frappe.get_doc("Import Expense", expense.name)
		exp_doc.landed_cost_allocated = 0
		exp_doc.landed_cost_voucher = None
		exp_doc.save()
	
	frappe.db.commit()
