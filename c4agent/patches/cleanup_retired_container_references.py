import frappe


RETIRED_DOCTYPES = ("Import Container", "Purchase Invoice Import Container")


def execute():
	"""Remove stale links that can load retired metadata while saving a document."""
	# Existing sites can have custom fields or older DocField rows beyond the
	# two integration fields removed by the original retirement patch.
	for table in ("Custom Field", "DocField"):
		frappe.db.delete(table, {
			"fieldtype": ("in", ["Link", "Table", "Table MultiSelect"]),
			"options": ("in", RETIRED_DOCTYPES),
		})
	frappe.db.delete("Property Setter", {
		"property": "options",
		"value": ("in", RETIRED_DOCTYPES),
	})
	frappe.db.delete("DocType Link", {"link_doctype": ("in", RETIRED_DOCTYPES)})
	frappe.clear_cache()
