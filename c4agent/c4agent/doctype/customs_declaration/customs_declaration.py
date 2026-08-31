import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CustomsDeclaration(Document):
	def validate(self):
		self.validate_shipment()
		self.validate_references()
		self.validate_status_transition()
		self.total_customs_cost = sum(
			flt(self.get(field))
			for field in (
				"customs_duty", "import_tax", "nafeza_fees", "inspection_fees",
				"quarantine_fees", "other_government_fees",
			)
		)

	def validate_status_transition(self):
		if self.is_new():
			self.clearance_status = "Draft"
			return
		old = self.get_doc_before_save()
		if not old or old.clearance_status == self.clearance_status:
			return
		allowed = {
			"Draft": ("Documents Submitted", "Cancelled"),
			"Documents Submitted": ("Under Review", "Cancelled"),
			"Under Review": ("Under Inspection", "Duties Assessed", "Cancelled"),
			"Under Inspection": ("Duties Assessed", "Cancelled"),
			"Duties Assessed": ("Payment Pending", "Cancelled"),
			"Payment Pending": ("Paid", "Cancelled"),
			"Paid": ("Released", "Cancelled"),
		}
		if self.clearance_status not in allowed.get(old.clearance_status, ()):
			frappe.throw(f"Cannot change Customs Declaration from {old.clearance_status} to {self.clearance_status}")
		if self.clearance_status in ("Documents Submitted", "Under Review") and not self.customs_declaration_number:
			frappe.throw("Customs Declaration Number is required")
		if self.clearance_status in ("Paid", "Released") and not self.accounting_references:
			frappe.throw("At least one ERPNext accounting reference is required")
		if self.clearance_status == "Released" and not self.release_date:
			frappe.throw("Release Date is required")
	def on_update(self):
		if self.clearance_status == "Released":
			frappe.db.set_value(
				"Import Shipment", self.import_shipment,
				{"customs_clearance_date": self.release_date or self.declaration_date},
				update_modified=False,
			)
			previous = self.get_doc_before_save()
			if not previous or previous.clearance_status != "Released":
				frappe.get_doc("Import Shipment", self.import_shipment).add_comment("Comment", f"Customs Declaration {self.name} released")

	def validate_shipment(self):
		shipment = frappe.db.get_value(
			"Import Shipment", self.import_shipment, ["company", "acid_number"], as_dict=True
		)
		if not shipment:
			frappe.throw("Import Shipment does not exist")
		if shipment.company != self.company:
			frappe.throw("Customs Declaration company must match Import Shipment company")
		self.acid_number = shipment.acid_number

	def validate_references(self):
		for row in self.accounting_references:
			if row.reference_doctype not in ("Purchase Invoice", "Journal Entry", "Payment Entry"):
				frappe.throw(f"Row {row.idx}: unsupported accounting reference type")
			if not frappe.db.exists(row.reference_doctype, row.reference_name):
				frappe.throw(f"Row {row.idx}: accounting reference does not exist")
