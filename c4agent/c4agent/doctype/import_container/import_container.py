# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ImportContainer(Document):
	"""Container tracking record linked to Import Shipment"""
	
	def validate(self):
		"""Validate container data"""
		self.normalize_container_number()
		self.validate_container_belongs_to_shipment()
		self.validate_unique_container_number()
		self.calculate_free_time_end_date()

	def on_update(self):
		"""Keep both the current and previous shipment summaries synchronized."""
		previous = self.get_doc_before_save()
		if previous and previous.import_shipment != self.import_shipment:
			update_shipment_container_summary(previous.import_shipment)
		update_shipment_container_summary(self.import_shipment)
		if previous and previous.container_status != self.container_status and self.container_status in ("Arrived", "Released"):
			frappe.get_doc("Import Shipment", self.import_shipment).add_comment("Comment", f"Container {self.container_number} marked {self.container_status}")

	def on_trash(self):
		"""Remove this container from its shipment summary before deletion."""
		update_shipment_container_summary(self.import_shipment, exclude_container=self.name)
	
	def normalize_container_number(self):
		"""Normalize container number: uppercase, remove spaces"""
		if self.container_number:
			self.container_number = "".join(self.container_number.upper().split())
	
	def validate_container_belongs_to_shipment(self):
		"""Validate selected container belongs to the shipment"""
		if self.import_shipment:
			# Verify shipment exists
			if not frappe.db.exists("Import Shipment", self.import_shipment):
				frappe.throw(frappe.exceptions.ValidationError(
					f"Import Shipment {self.import_shipment} does not exist"
				))
	
	def validate_unique_container_number(self):
		"""Reject duplicate physical container numbers with a useful error."""
		existing = frappe.db.get_value(
			"Import Container",
			{"container_number": self.container_number, "name": ("!=", self.name)},
			"name"
		)
		if existing:
			frappe.throw(
				f"Container number {self.container_number} already exists as {existing}"
			)
	
	def calculate_free_time_end_date(self):
		"""Calculate free_time_end_date = arrival_date + free_days"""
		if self.arrival_date and self.free_days:
			from datetime import timedelta
			self.free_time_end_date = self.arrival_date + timedelta(days=self.free_days)
	
	def calculate_container_costs(self):
		"""Calculate total container cost from linked Import Expenses"""
		if not self.name:
			self.total_container_cost = 0
			return
		
		cost_fields = ["freight_cost", "port_cost", "storage_cost", "demurrage_cost", 
		               "transportation_cost", "other_cost"]
		
		# Reset all cost fields
		for field in cost_fields:
			setattr(self, field, 0)
		
		# Query Import Expenses linked to this container
		self.total_container_cost = 0
		if frappe.db.exists("DocType", "Import Expense"):
			expenses = frappe.get_all(
				"Import Expense",
				filters={
					"import_container": self.name,
					"docstatus": 1
				},
				fields=["expense_type", "base_amount"]
			)
			
			# Aggregate by type (simplified - would need actual expense type linking)
			total = 0
			for expense in expenses:
				total += expense.base_amount or 0
			
			self.total_container_cost = total


def update_shipment_container_summary(shipment_name, exclude_container=None):
	"""Update stored shipment container totals without recursively saving the shipment."""
	if not shipment_name or not frappe.db.exists("Import Shipment", shipment_name):
		return

	filters = {"import_shipment": shipment_name}
	if exclude_container:
		filters["name"] = ("!=", exclude_container)

	containers = frappe.get_all(
		"Import Container",
		filters=filters,
		fields=["packages", "gross_weight", "cbm"],
	)
	frappe.db.set_value(
		"Import Shipment",
		shipment_name,
		{
			"container_count": len(containers),
			"total_packages": sum(row.packages or 0 for row in containers),
			"total_gross_weight": sum(row.gross_weight or 0 for row in containers),
			"total_cbm": sum(row.cbm or 0 for row in containers),
		},
		update_modified=False,
	)
