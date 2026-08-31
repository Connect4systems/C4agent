import frappe
from frappe.utils import nowdate


def update_sinosure_expiry_status():
	"""Expire active coverages after their contractual expiry date."""
	for name in frappe.get_all("Sinosure Coverage", filters={
		"coverage_status": "Active", "coverage_expiry_date": ("<", nowdate()),
	}, pluck="name"):
		frappe.db.set_value("Sinosure Coverage", name, "coverage_status", "Expired")
