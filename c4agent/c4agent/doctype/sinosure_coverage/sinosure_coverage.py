import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate


class SinosureCoverage(Document):
	def validate(self):
		shipment = frappe.get_doc("Import Shipment", self.import_shipment)
		if shipment.company != self.company or shipment.supplier != self.supplier:
			frappe.throw("Sinosure Coverage must match the shipment company and supplier")
		if self.coverage_start_date and self.coverage_expiry_date and getdate(self.coverage_expiry_date) < getdate(self.coverage_start_date):
			frappe.throw("Coverage Expiry Date cannot be before Coverage Start Date")
		self.remaining_limit = flt(self.approved_limit) - flt(self.opening_or_previous_exposure) - flt(self.current_shipment_exposure)
		self.fee_base_amount = flt(self.fee_amount) * flt(self.fee_exchange_rate or 1)
		if self.remaining_limit < 0:
			if not self.override_reason:
				frappe.throw("Sinosure exposure exceeds the approved limit; an override reason is required")
			if "Finance Manager" not in frappe.get_roles():
				frappe.throw("Only a Finance Manager can approve a Sinosure limit override")
		if self.coverage_status == "Active" and self.coverage_expiry_date and getdate(self.coverage_expiry_date) < getdate(nowdate()):
			frappe.throw("Expired coverage cannot be Active")

	def on_update(self):
		if self.coverage_status in ("Approved", "Active"):
			frappe.db.set_value("Import Shipment", self.import_shipment, {
				"sinosure_coverage": self.name,
				"sinosure_exposure_amount": self.current_shipment_exposure,
			}, update_modified=False)
		previous = self.get_doc_before_save()
		if previous and flt(previous.approved_limit) != flt(self.approved_limit):
			self.add_comment("Comment", f"Approved limit changed from {previous.approved_limit} to {self.approved_limit}")
