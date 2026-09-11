# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


SUPPORTED_ACCOUNTING_REFERENCES = ("Purchase Invoice", "Journal Entry", "Payment Entry")


class ImportExpense(Document):
	"""Operational cost attribution linked to standard ERPNext accounting records."""

	def before_validate(self):
		self.fetch_supplier_invoice_amount()
		self.apply_expense_type_defaults()
		self.apply_accounting_defaults()
		self.set_currency_values()
		if self.docstatus == 0:
			self.total_paid = 0
			self.outstanding_amount = self.amount
			self.payment_status = "Unpaid"

	def fetch_supplier_invoice_amount(self):
		if self.docstatus != 0 or not self.supplier_invoice:
			return
		previous = self.get_doc_before_save()
		if previous and previous.supplier_invoice == self.supplier_invoice:
			return
		invoice = frappe.get_doc("Purchase Invoice", self.supplier_invoice)
		invoice.check_permission("read")
		self.supplier = invoice.supplier
		self.currency = invoice.currency
		self.amount = invoice.grand_total if invoice.disable_rounded_total else invoice.rounded_total or invoice.grand_total
		self.exchange_rate = invoice.conversion_rate

	def validate(self):
		self.validate_shipment()
		self.validate_supplier_invoice()
		self.validate_amount_and_exchange_rate()
		self.validate_expense_account()
		self.validate_accounting_reference()
		self.validate_recoverable_tax_policy()
		self.warn_duplicate_expense()

	def before_submit(self):
		if self.expense_status not in ("Approved", "Allocated"):
			frappe.throw("Import Expense must be approved through the finance workflow")

	def before_cancel(self):
		from c4agent.c4agent.services.expense_payment import payment_totals
		if payment_totals(self)[0] > 0:
			frappe.throw("Cancel the payment Journal Entries before cancelling this expense")
		if self.landed_cost_allocated:
			frappe.throw("Cancel the linked Landed Cost Voucher before cancelling this expense")

	def on_submit(self):
		refresh_import_expense_summaries(self.import_shipment)
		if self.landed_cost_override_reason:
			frappe.get_doc("Import Shipment", self.import_shipment).add_comment("Comment", f"Import Expense {self.name} landed-cost policy overridden: {self.landed_cost_override_reason}")

	def on_cancel(self):
		refresh_import_expense_summaries(
			self.import_shipment,
			exclude_expense=self.name,
		)

	def apply_expense_type_defaults(self):
		if not self.expense_type:
			return

		previous = self.get_doc_before_save()
		if previous and previous.expense_type == self.expense_type:
			return

		expense_type = frappe.db.get_value(
			"Import Expense Type",
			self.expense_type,
			[
				"default_expense_account",
				"include_in_landed_cost",
				"is_recoverable_tax",
				"allocation_basis",
				"disabled",
			],
			as_dict=True,
		)
		if not expense_type:
			return
		if expense_type.disabled:
			frappe.throw(f"Import Expense Type {self.expense_type} is disabled")

		if expense_type.default_expense_account:
			self.expense_account = expense_type.default_expense_account
		self.include_in_landed_cost = 0 if expense_type.is_recoverable_tax else (
			expense_type.include_in_landed_cost
		)
		self.allocation_basis = expense_type.allocation_basis or "Amount"

	def set_currency_values(self):
		if not self.company:
			return

		self.company_currency = frappe.db.get_value("Company", self.company, "default_currency")
		if not self.currency:
			self.currency = self.company_currency
		if self.currency == self.company_currency:
			self.exchange_rate = 1

		self.base_amount = flt(
			flt(self.amount) * flt(self.exchange_rate),
			self.precision("base_amount"),
		)

	def apply_accounting_defaults(self):
		settings = frappe.get_single("C4agent Settings")
		if not self.cost_center:
			self.cost_center = settings.default_import_expense_cost_center
		if not self.project:
			self.project = settings.default_import_expense_project

	def validate_shipment(self):
		shipment = frappe.db.get_value(
			"Import Shipment",
			self.import_shipment,
			["company", "shipment_status"],
			as_dict=True,
		)
		if not shipment:
			frappe.throw(f"Import Shipment {self.import_shipment} does not exist")
		if shipment.company != self.company:
			frappe.throw(
				f"Import Expense company {self.company} does not match shipment company {shipment.company}"
			)
		if shipment.shipment_status in ("Closed", "Cancelled"):
			frappe.throw(f"Cannot add or change expenses on a {shipment.shipment_status} shipment")

	def validate_supplier_invoice(self):
		if not self.supplier_invoice:
			return

		invoice = frappe.db.get_value(
			"Purchase Invoice",
			self.supplier_invoice,
			["company", "supplier", "custom_import_shipment", "docstatus"],
			as_dict=True,
		)
		if not invoice:
			frappe.throw(f"Purchase Invoice {self.supplier_invoice} does not exist")
		if invoice.company != self.company:
			frappe.throw("Supplier Invoice company does not match Import Expense company")
		if invoice.docstatus != 1:
			frappe.throw("Supplier Invoice must be submitted")
		if self.supplier and invoice.supplier != self.supplier:
			frappe.throw("Supplier Invoice supplier does not match Import Expense supplier")
		if invoice.custom_import_shipment and invoice.custom_import_shipment != self.import_shipment:
			frappe.throw("Supplier Invoice is linked to a different Import Shipment")
		if not self.supplier:
			self.supplier = invoice.supplier
		if not self.accounting_reference_doctype and not self.accounting_reference_name:
			self.accounting_reference_doctype = "Purchase Invoice"
			self.accounting_reference_name = self.supplier_invoice

	def validate_amount_and_exchange_rate(self):
		if flt(self.amount) <= 0:
			frappe.throw("Amount must be greater than zero")
		if flt(self.exchange_rate) <= 0:
			frappe.throw("Exchange Rate must be greater than zero")

	def validate_expense_account(self):
		account = frappe.db.get_value(
			"Account",
			self.expense_account,
			["company", "is_group"],
			as_dict=True,
		)
		if not account:
			frappe.throw(f"Account {self.expense_account} does not exist")
		if account.company != self.company:
			frappe.throw(f"Account {self.expense_account} does not belong to company {self.company}")
		if account.is_group:
			frappe.throw(f"Account {self.expense_account} must not be a group account")
		if self.cost_center and frappe.db.get_value("Cost Center", self.cost_center, "company") != self.company:
			frappe.throw(f"Cost Center {self.cost_center} does not belong to company {self.company}")
		if self.project:
			project_company = frappe.db.get_value("Project", self.project, "company")
			if project_company and project_company != self.company:
				frappe.throw(f"Project {self.project} does not belong to company {self.company}")

	def validate_accounting_reference(self):
		if bool(self.accounting_reference_doctype) != bool(self.accounting_reference_name):
			frappe.throw("Accounting Reference Type and Accounting Reference must be set together")
		if not self.accounting_reference_doctype:
			return
		if self.accounting_reference_doctype not in SUPPORTED_ACCOUNTING_REFERENCES:
			frappe.throw("Accounting Reference Type must be Purchase Invoice, Journal Entry, or Payment Entry")
		if not frappe.db.exists(self.accounting_reference_doctype, self.accounting_reference_name):
			frappe.throw(
				f"{self.accounting_reference_doctype} {self.accounting_reference_name} does not exist"
			)

	def validate_recoverable_tax_policy(self):
		is_recoverable_tax = frappe.db.get_value(
			"Import Expense Type", self.expense_type, "is_recoverable_tax"
		)
		if not is_recoverable_tax or not self.include_in_landed_cost:
			return

		roles = set(frappe.get_roles())
		if not roles.intersection({"Finance Manager", "System Manager"}):
			frappe.throw("Only a Finance Manager can capitalize a recoverable tax")
		if not self.landed_cost_override_reason:
			frappe.throw("Landed Cost Override Reason is required for a recoverable tax")

	def warn_duplicate_expense(self):
		filters = {
			"name": ("!=", self.name),
			"docstatus": ("!=", 2),
			"import_shipment": self.import_shipment,
			"expense_type": self.expense_type,
			"supplier": self.supplier or "",
			"supplier_invoice": self.supplier_invoice or "",
			"currency": self.currency,
			"amount": self.amount,
		}
		existing = frappe.db.get_value("Import Expense", filters, "name")
		if existing:
			frappe.msgprint(
				f"A similar Import Expense already exists: {existing}",
				alert=True,
				indicator="orange",
			)


def refresh_import_expense_summaries(shipment_name, exclude_expense=None):
	"""Refresh shipment base-currency expense summaries."""
	filters = {"import_shipment": shipment_name, "docstatus": 1}
	if exclude_expense:
		filters["name"] = ("!=", exclude_expense)

	shipment_expenses = frappe.get_all(
		"Import Expense",
		filters=filters,
		fields=["base_amount"],
	)
	frappe.db.set_value(
		"Import Shipment",
		shipment_name,
		"total_import_expenses",
		sum(row.base_amount or 0 for row in shipment_expenses),
		update_modified=False,
	)
