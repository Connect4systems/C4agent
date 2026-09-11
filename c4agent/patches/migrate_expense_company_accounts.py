import frappe


def execute():
	"""Preserve legacy defaults under the company that owns each account."""
	if not frappe.db.has_column("Import Expense Type", "default_expense_account"):
		return
	for row in frappe.db.sql("""
		select t.name, t.default_expense_account, a.company
		from `tabImport Expense Type` t
		inner join `tabAccount` a on a.name=t.default_expense_account
		where coalesce(t.default_expense_account, '') != ''
	""", as_dict=True):
		doc = frappe.get_doc("Import Expense Type", row.name)
		if any(account.company == row.company for account in doc.company_accounts):
			continue
		# Preserve historical defaults even when they need review under the new rules.
		doc.append("company_accounts", {
			"company": row.company, "default_expense_account": row.default_expense_account,
		}).db_insert()
	frappe.clear_cache(doctype="Import Expense Type")
