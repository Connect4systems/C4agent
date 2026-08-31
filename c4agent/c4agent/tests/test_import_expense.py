# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

from datetime import date

import frappe
from frappe.tests.utils import FrappeTestCase


class TestImportExpense(FrappeTestCase):
	"""Import expense attribution and accounting-safety tests."""

	def setUp(self):
		super().setUp()
		self.company = frappe.db.get_value("Company", {"is_group": 0}, "name")
		self.assertIsNotNone(self.company, "ERPNext test site must contain a test Company")
		self.company_currency = frappe.db.get_value("Company", self.company, "default_currency")
		self.foreign_currency = "USD" if self.company_currency != "USD" else "EUR"
		self.account = frappe.db.get_value(
			"Account",
			{"company": self.company, "is_group": 0},
			"name",
		)
		self.assertIsNotNone(self.account, "ERPNext test Company must contain a ledger Account")
		self.supplier = self.get_or_create_supplier()
		self.purchase_order = self.create_purchase_order()
		self.shipment = self.create_shipment()

	def get_or_create_supplier(self):
		name = "_Test C4agent Import Supplier"
		if not frappe.db.exists("Supplier", name):
			frappe.get_doc(
				{
					"doctype": "Supplier",
					"supplier_name": name,
					"supplier_type": "Company",
				}
			).insert(ignore_permissions=True)
		return name

	def get_or_create_item(self):
		item_code = "_TEST-C4-IMPORT-ITEM"
		if not frappe.db.exists("Item", item_code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": "C4agent Import Expense Test Item",
					"item_group": "All Item Groups",
					"stock_uom": "Nos",
				}
			).insert(ignore_permissions=True)
		return item_code

	def create_purchase_order(self):
		purchase_order = frappe.get_doc(
			{
				"doctype": "Purchase Order",
				"supplier": self.supplier,
				"company": self.company,
				"transaction_date": date.today(),
				"items": [
					{
						"item_code": self.get_or_create_item(),
						"qty": 10,
						"rate": 100,
					}
				],
			}
		).insert()
		purchase_order.submit()
		return purchase_order.name

	def create_shipment(self):
		return frappe.get_doc(
			{
				"doctype": "Import Shipment",
				"company": self.company,
				"supplier": self.supplier,
				"purchase_order": self.purchase_order,
			}
		).insert()

	def make_expense(self, expense_type="Ocean Freight", **values):
		data = {
			"doctype": "Import Expense",
			"company": self.company,
			"posting_date": date.today(),
			"import_shipment": self.shipment.name,
			"expense_type": expense_type,
			"currency": self.foreign_currency,
			"exchange_rate": 50,
			"amount": 100,
			"expense_account": self.account,
		}
		data.update(values)
		return frappe.get_doc(data)

	def test_import_expense_base_amount(self):
		expense = self.make_expense().insert()

		self.assertEqual(expense.base_amount, 5000)
		self.assertEqual(expense.include_in_landed_cost, 1)
		self.assertEqual(expense.allocation_basis, "Amount")

	def test_container_must_belong_to_expense_shipment(self):
		other_shipment = self.create_shipment()
		other_container = frappe.get_doc(
			{
				"doctype": "Import Container",
				"import_shipment": other_shipment.name,
				"container_number": "EXPENSE-MISMATCH-001",
			}
		).insert()

		with self.assertRaises(frappe.ValidationError):
			self.make_expense(import_container=other_container.name).insert()

	def test_recoverable_import_vat_excluded_by_default(self):
		expense = self.make_expense(expense_type="Import VAT").insert()

		self.assertEqual(expense.include_in_landed_cost, 0)

	def test_recoverable_tax_override_requires_reason(self):
		expense = self.make_expense(expense_type="Import VAT").insert()
		expense.include_in_landed_cost = 1

		with self.assertRaises(frappe.ValidationError):
			expense.save()

	def test_account_must_belong_to_company(self):
		other_account = frappe.db.get_value(
			"Account",
			{"company": ("!=", self.company), "is_group": 0},
			"name",
		)
		if not other_account:
			self.skipTest("A second test Company is required for cross-company account validation")

		with self.assertRaises(frappe.ValidationError):
			self.make_expense(expense_account=other_account).insert()


class TestImportExpenseSetup(FrappeTestCase):
	def test_seeded_types_and_workflow_exist(self):
		for expense_type in ("Ocean Freight", "Customs Duty", "Import VAT", "Port Charges"):
			self.assertTrue(frappe.db.exists("Import Expense Type", expense_type))

		self.assertTrue(
			frappe.db.exists(
				"Workflow",
				{
					"workflow_name": "Import Expense Approval",
					"document_type": "Import Expense",
					"is_active": 1,
				},
			)
		)
