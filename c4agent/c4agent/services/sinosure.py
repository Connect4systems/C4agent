import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_supplier_sinosure_exposure(supplier, company):
	frappe.has_permission("Sinosure Coverage", "read", throw=True)
	rows = frappe.get_all("Sinosure Coverage", filters={
		"supplier": supplier, "company": company, "coverage_status": ("in", ("Approved", "Active")),
	}, fields=["approved_limit", "opening_or_previous_exposure", "current_shipment_exposure", "import_shipment"])
	approved = sum(flt(row.approved_limit) for row in rows)
	active = sum(flt(row.opening_or_previous_exposure) + flt(row.current_shipment_exposure) for row in rows)
	return {
		"approved_limit": approved,
		"active_exposure": active,
		"available_limit": approved - active,
		"open_shipments": [row.import_shipment for row in rows],
	}
