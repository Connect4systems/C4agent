# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe


def validate_import_shipment(doc, method=None):
	"""
	Validate Landed Cost Voucher has matching Import Shipment
	"""
	if not getattr(doc, "custom_import_shipment", None):
		return
	
	if not frappe.db.exists("Import Shipment", doc.custom_import_shipment):
		frappe.throw(f"Import Shipment {doc.custom_import_shipment} does not exist")

	for row in doc.purchase_receipts:
		linked_shipment = frappe.db.get_value(row.receipt_document_type, row.receipt_document, "custom_import_shipment")
		if linked_shipment != doc.custom_import_shipment:
			frappe.throw(f"Receipt {row.receipt_document} is not linked to Import Shipment {doc.custom_import_shipment}")

	seen = set()
	for row in doc.taxes:
		expense_name = getattr(row, "custom_import_expense", None)
		if not expense_name:
			frappe.throw(f"Landed cost row {row.idx} must reference its exact Import Expense")
		if expense_name in seen:
			frappe.throw(f"Import Expense {expense_name} is referenced more than once")
		seen.add(expense_name)
		expense = frappe.get_doc("Import Expense", expense_name)
		if expense.import_shipment != doc.custom_import_shipment or expense.docstatus != 1:
			frappe.throw(f"Import Expense {expense_name} is not an approved expense for this shipment")
		if expense.landed_cost_allocated and expense.landed_cost_voucher != doc.name:
			frappe.throw(f"Import Expense {expense_name} is already allocated to {expense.landed_cost_voucher}")
		if abs(float(row.base_amount or 0) - float(expense.base_amount or 0)) > 0.01:
			frappe.throw(f"Landed cost row for {expense_name} must equal its company-currency amount")


def on_submit(doc, method=None):
	if not getattr(doc, "custom_import_shipment", None):
		return
	for row in doc.taxes:
		if getattr(row, "custom_import_expense", None):
			frappe.db.set_value("Import Expense", row.custom_import_expense, {
				"landed_cost_allocated": 1, "landed_cost_voucher": doc.name, "expense_status": "Allocated",
			})
	refresh_landed_cost_summary(doc.custom_import_shipment)
	frappe.get_doc("Import Shipment", doc.custom_import_shipment).add_comment("Comment", f"Landed Cost Voucher {doc.name} submitted")


def on_cancel(doc, method=None):
	if not getattr(doc, "custom_import_shipment", None):
		return
	for row in doc.taxes:
		if getattr(row, "custom_import_expense", None) and frappe.db.get_value("Import Expense", row.custom_import_expense, "landed_cost_voucher") == doc.name:
			frappe.db.set_value("Import Expense", row.custom_import_expense, {
				"landed_cost_allocated": 0, "landed_cost_voucher": None, "expense_status": "Approved",
			})
	refresh_landed_cost_summary(doc.custom_import_shipment, exclude_voucher=doc.name)
	frappe.get_doc("Import Shipment", doc.custom_import_shipment).add_comment("Comment", f"Landed Cost Voucher {doc.name} cancelled")


def refresh_landed_cost_summary(shipment, exclude_voucher=None):
	filters = {"custom_import_shipment": shipment, "docstatus": 1}
	if exclude_voucher:
		filters["name"] = ("!=", exclude_voucher)
	total = sum(row.total_taxes_and_charges or 0 for row in frappe.get_all(
		"Landed Cost Voucher", filters=filters, fields=["total_taxes_and_charges"]
	))
	frappe.db.set_value("Import Shipment", shipment, "total_landed_cost", total, update_modified=False)
