# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ImportExpenseType(Document):
	"""Finance-controlled classification and landed-cost policy for import costs."""

	def validate(self):
		companies = set()
		for row in self.company_accounts:
			if row.company in companies:
				frappe.throw(f"Only one default account is allowed for company {row.company}")
			companies.add(row.company)
			validate_company_account(row.default_expense_account, row.company, self.is_recoverable_tax)


def validate_company_account(name, company, recoverable=False):
	account = frappe.get_doc("Account", name)
	if account.company != company or account.is_group or account.disabled:
		frappe.throw("Select an enabled, non-group account belonging to the selected company")
	if account.root_type != "Expense" and not (
		recoverable and (account.root_type == "Asset" or account.account_type == "Tax")
	):
		frappe.throw("Select an Expense account; recoverable-tax types also allow Asset or Tax accounts")


@frappe.whitelist()
def get_company_defaults(expense_type, company):
	doc = frappe.get_doc("Import Expense Type", expense_type)
	doc.check_permission("read")
	return {
		"default_expense_account": next((row.default_expense_account for row in doc.company_accounts if row.company == company), None),
		"is_recoverable_tax": doc.is_recoverable_tax,
		"include_in_landed_cost": doc.include_in_landed_cost,
		"allocation_basis": doc.allocation_basis,
		"disabled": doc.disabled,
	}
