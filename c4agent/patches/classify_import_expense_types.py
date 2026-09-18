import frappe


def execute():
	"""Classify legacy user-created types as ordinary import expenses."""
	if frappe.db.exists("DocType", "Import Expense Type"):
		frappe.db.sql("""update `tabImport Expense Type`
			set type='Import Expenses' where coalesce(type, '')=''""")
		frappe.db.sql("""update `tabImport Expense Type`
			set type='Customs Declaration' where type='Customs Clearance'""")
	frappe.clear_cache(doctype="Import Expense Type")
