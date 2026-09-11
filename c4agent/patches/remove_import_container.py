import frappe


def execute():
	"""Retire container metadata while retaining historical database tables."""
	if frappe.db.exists("DocType", "Import Container"):
		# Use SQL because the retired controller is no longer shipped with the app.
		for row in frappe.db.sql("""
			select import_shipment, count(*) as container_count
			from `tabImport Container` group by import_shipment
		""", as_dict=True):
			frappe.db.set_value("Import Shipment", row.import_shipment,
				"container_count", row.container_count, update_modified=False)

	for name in (
		"Purchase Invoice-custom_import_containers",
		"Purchase Receipt Item-custom_import_container",
	):
		frappe.delete_doc("Custom Field", name, ignore_permissions=True)

	for table, field in (("Workspace Link", "link_to"), ("Workspace Shortcut", "link_to")):
		frappe.db.delete(table, {field: ("in", ["Import Container", "Container Cost Summary"])})
	frappe.delete_doc("Report", "Container Cost Summary", force=True, ignore_permissions=True)
	for name in ("Purchase Invoice Import Container", "Import Container"):
		frappe.delete_doc("DocType", name, force=True, ignore_permissions=True)
	frappe.clear_cache()
