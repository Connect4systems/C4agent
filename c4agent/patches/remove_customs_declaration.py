import frappe


DECLARATION_STATUS_MAP = {
	"Draft": "Under Customs Clearance",
	"Documents Submitted": "Documents Submitted",
	"Under Review": "Under Review",
	"Under Inspection": "Under Inspection",
	"Duties Assessed": "Duties Assessed",
	"Payment Pending": "Duties Assessed",
	"Paid": "Duties Assessed",
	"Released": "Cleared",
}
TERMINAL_SHIPMENT_STATUSES = {"Received", "Closed", "Cancelled"}
STATUS_PRIORITY = {status: index for index, status in enumerate(DECLARATION_STATUS_MAP)}


def execute():
	"""Move declaration progress onto shipments, then retire its schema and links."""
	if frappe.db.exists("DocType", "Customs Declaration"):
		declarations = frappe.get_all(
			"Customs Declaration",
			fields=["import_shipment", "clearance_status", "release_date", "declaration_date"],
		)
		latest_by_shipment = {}
		for declaration in declarations:
			current = latest_by_shipment.get(declaration.import_shipment)
			if not current or STATUS_PRIORITY.get(declaration.clearance_status, -1) > STATUS_PRIORITY.get(current.clearance_status, -1):
				latest_by_shipment[declaration.import_shipment] = declaration

		for declaration in latest_by_shipment.values():
			if not frappe.db.exists("Import Shipment", declaration.import_shipment):
				continue
			shipment = frappe.db.get_value(
				"Import Shipment", declaration.import_shipment,
				["shipment_status", "customs_clearance_date"], as_dict=True,
			)
			if shipment.shipment_status not in TERMINAL_SHIPMENT_STATUSES:
				status = DECLARATION_STATUS_MAP.get(declaration.clearance_status)
				if status:
					frappe.db.set_value(
						"Import Shipment", declaration.import_shipment, "shipment_status", status,
						update_modified=False,
					)
			if declaration.clearance_status == "Released" and not shipment.customs_clearance_date:
				frappe.db.set_value(
					"Import Shipment", declaration.import_shipment,
					"customs_clearance_date", declaration.release_date or declaration.declaration_date,
					update_modified=False,
				)

	for table in ("Custom Field", "DocField"):
		frappe.db.delete(table, {
			"fieldtype": ("in", ["Link", "Table", "Table MultiSelect"]),
			"options": ("in", ["Customs Declaration", "Customs Accounting Reference"]),
		})
	frappe.db.delete("Property Setter", {
		"property": "options",
		"value": ("in", ["Customs Declaration", "Customs Accounting Reference"]),
	})
	frappe.db.delete("DocType Link", {
		"link_doctype": ("in", ["Customs Declaration", "Customs Accounting Reference"]),
	})
	for table, field in (("Workspace Link", "link_to"), ("Workspace Shortcut", "link_to")):
		frappe.db.delete(table, {field: "Customs Declaration"})

	if frappe.db.exists("Workflow", "Customs Declaration Lifecycle"):
		frappe.delete_doc("Workflow", "Customs Declaration Lifecycle", force=True, ignore_permissions=True)
	for action in ("Confirm Customs Release", "Request Payment", "Confirm Payment", "Cancel Declaration"):
		if frappe.db.exists("Workflow Action Master", action):
			frappe.delete_doc("Workflow Action Master", action, force=True, ignore_permissions=True)
	frappe.db.sql("""update `tabImport Expense Type`
		set type='Customs Clearance' where type='Customs Declaration'""")
	for doctype in ("Customs Accounting Reference", "Customs Declaration"):
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True)
	frappe.clear_cache()
