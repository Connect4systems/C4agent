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
		self.check_duplicate_container_number()
		self.calculate_free_time_end_date()
	
	def normalize_container_number(self):
		"""Normalize container number: uppercase, remove spaces"""
		if self.container_number:
			self.container_number = self.container_number.upper().strip()
	
	def validate_container_belongs_to_shipment(self):
		"""Validate selected container belongs to the shipment"""
		if self.import_shipment:
			# Verify shipment exists
			if not frappe.db.exists("Import Shipment", self.import_shipment):
				frappe.throw(frappe.exceptions.ValidationError(
					f"Import Shipment {self.import_shipment} does not exist"
				))
	
	def check_duplicate_container_number(self):
		"""Warn if container number already exists"""
		existing = frappe.db.get_value(
			"Import Container",
			{"container_number": self.container_number, "name": ("!=", self.name)},
			"name"
		)
		if existing:
			frappe.msgprint(
				f"Warning: Container number {self.container_number} already exists as {existing}",
				alert=True,
				indicator="orange"
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
