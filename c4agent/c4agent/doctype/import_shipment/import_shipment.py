# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class ImportShipment(Document):
	"""
	Central operational record for import shipments.
	Tracks purchase order -> shipment -> containers -> customs -> receipt -> landed cost
	"""
	
	def validate(self):
		"""Validate shipment data"""
		self.generate_shipment_title()
		self.validate_supplier_company_match()
		self.validate_purchase_order()
		self.validate_eta_after_etd()
		self.validate_status_transition()
		self.refresh_summary_totals()
	
	def before_save(self):
		"""Auto-fetch supplier currency from PO"""
		if self.purchase_order and not self.supplier_currency:
			po = frappe.get_doc("Purchase Order", self.purchase_order)
			if po.currency:
				self.supplier_currency = po.currency
	
	def generate_shipment_title(self):
		"""Auto-generate shipment_title if not set"""
		if self.company and self.supplier and self.purchase_order:
			self.shipment_title = f"{self.supplier} / {self.purchase_order} / {self.port_of_loading or 'Origin'} -> {self.port_of_discharge or 'Dest'}"
	
	def validate_supplier_company_match(self):
		"""Validate supplier and company exist and match PO if provided"""
		if self.company and not frappe.db.exists("Company", self.company):
			frappe.throw(f"Company {self.company} does not exist")
		
		if self.supplier and not frappe.db.exists("Supplier", self.supplier):
			frappe.throw(f"Supplier {self.supplier} does not exist")
		
		if self.purchase_order:
			po = frappe.get_doc("Purchase Order", self.purchase_order)
			if po.company != self.company:
				frappe.throw(f"PO company {po.company} does not match shipment company {self.company}")
			if po.supplier != self.supplier:
				frappe.throw(f"PO supplier {po.supplier} does not match shipment supplier {self.supplier}")
	
	def validate_purchase_order(self):
		"""Validate PO is submitted and active"""
		if self.purchase_order:
			po = frappe.get_doc("Purchase Order", self.purchase_order)
			if po.docstatus != 1:
				frappe.throw(f"Purchase Order {self.purchase_order} must be submitted")
			if po.status in ["Cancelled"]:
				frappe.throw(f"Cannot use Cancelled Purchase Order")
	
	def validate_eta_after_etd(self):
		"""Validate ETA is not before ETD"""
		if self.etd and self.eta and self.eta < self.etd:
			frappe.throw("ETA cannot be before ETD")
	
	def validate_status_transition(self):
		"""Validate allowed status transitions"""
		if self.is_new():
			self.shipment_status = "Draft"
			return
		
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return
		
		old_status = old_doc.shipment_status
		new_status = self.shipment_status
		
		# Define allowed transitions
		allowed_transitions = {
			"Draft": ["Ordered", "Cancelled"],
			"Ordered": ["Booked", "Cancelled"],
			"Booked": ["In Transit", "Cancelled"],
			"In Transit": ["Arrived", "Cancelled"],
			"Arrived": ["Under Customs Clearance", "Cancelled"],
			"Under Customs Clearance": ["Cleared", "Cancelled"],
			"Cleared": ["Received", "Cancelled"],
			"Received": ["Closed", "Cancelled"],
		}
		
		if old_status == new_status:
			return
		
		if old_status not in allowed_transitions:
			frappe.throw(f"Invalid status: {old_status}")
		
		if new_status not in allowed_transitions.get(old_status, []):
			frappe.throw(f"Cannot transition from {old_status} to {new_status}")
		
		if new_status == "Cancelled":
			self.validate_cancellation()
			return

		# Validate prerequisites for status transitions
		self.validate_status_prerequisites(new_status)
	
	def validate_status_prerequisites(self, new_status):
		"""Validate prerequisites before allowing status change"""
		if new_status == "Ordered":
			if not self.purchase_order:
				frappe.throw("Purchase Order must be set before Ordered status")
		
		elif new_status == "Booked":
			if not self.shipping_line:
				frappe.throw("Shipping Line is required before confirming a booking")
			if not self.etd and not self.actual_departure_date:
				frappe.throw("ETD or Actual Departure Date is required before confirming a booking")
		
		elif new_status == "In Transit":
			if not self.actual_departure_date:
				frappe.throw("Actual Departure Date is required before confirming departure")
			settings = frappe.get_single("C4agent Settings")
			if settings.require_acid_before_departure and not self.acid_number:
				frappe.throw("ACID Number is required before confirming departure")
		
		elif new_status == "Arrived":
			if not self.actual_arrival_date:
				frappe.throw("Actual Arrival Date is required before confirming arrival")
		
		elif new_status == "Under Customs Clearance":
			if not frappe.db.exists("DocType", "Customs Declaration"):
				frappe.throw("Customs Declaration must be installed before starting customs clearance")
			customs = frappe.db.get_value(
				"Customs Declaration",
				{"import_shipment": self.name},
				"name"
			)
			if not customs:
				frappe.throw("At least one Customs Declaration is required")
		
		elif new_status == "Cleared":
			if not frappe.db.exists("DocType", "Customs Declaration"):
				frappe.throw("Customs Declaration must be installed before confirming clearance")
			customs = frappe.db.get_value(
				"Customs Declaration",
				{"import_shipment": self.name, "clearance_status": "Released"},
				"name"
			)
			if not customs:
				frappe.throw("At least one Customs Declaration must be Released")
		
		elif new_status == "Received":
			pr = frappe.db.get_value(
				"Purchase Receipt",
				{"custom_import_shipment": self.name, "docstatus": 1},
				"name"
			)
			if not pr:
				frappe.throw("At least one submitted Purchase Receipt is required")

		elif new_status == "Closed":
			self.validate_basic_closure()
			self.closed_on = now_datetime()
			self.closed_by = frappe.session.user

	def validate_cancellation(self):
		"""Block operational cancellation while submitted ERPNext documents remain linked."""
		linked_documents = (
			("Purchase Invoice", "custom_import_shipment"),
			("Purchase Receipt", "custom_import_shipment"),
			("Landed Cost Voucher", "custom_import_shipment"),
		)
		for doctype, fieldname in linked_documents:
			if frappe.db.exists(doctype, {fieldname: self.name, "docstatus": 1}):
				frappe.throw(f"Cancel submitted {doctype} documents linked to this shipment first")

	def validate_basic_closure(self):
		"""Apply the Phase 0 closure gate; financial closure is strengthened in Milestone 4."""
		if not frappe.db.exists(
			"Purchase Receipt",
			{"custom_import_shipment": self.name, "docstatus": 1},
		):
			frappe.throw("At least one submitted Purchase Receipt is required before closing")

		settings = frappe.get_single("C4agent Settings")
		if settings.require_landed_cost_before_closing and not frappe.db.exists(
			"Landed Cost Voucher",
			{"custom_import_shipment": self.name, "docstatus": 1},
		):
			frappe.throw("A submitted Landed Cost Voucher is required before closing")
	
	def refresh_summary_totals(self):
		"""Calculate summary totals from linked records"""
		self.container_count = frappe.db.count("Import Container", {"import_shipment": self.name})
		
		containers = frappe.get_all(
			"Import Container",
			filters={"import_shipment": self.name},
			fields=["COUNT(*) as cnt", "SUM(packages) as pkg", "SUM(gross_weight) as gw", "SUM(cbm) as cbm"]
		)
		
		if containers and containers[0]:
			self.total_packages = containers[0].pkg or 0
			self.total_gross_weight = containers[0].gw or 0
			self.total_cbm = containers[0].cbm or 0
		
		# Total import expenses (company currency)
		self.total_import_expenses = 0
		if frappe.db.exists("DocType", "Import Expense"):
			expenses = frappe.get_all(
				"Import Expense",
				filters={"import_shipment": self.name, "docstatus": 1},
				fields=["SUM(base_amount) as total"]
			)
			self.total_import_expenses = expenses[0].total if expenses else 0
		
		# Fetch PO value
		if self.purchase_order:
			po_total = frappe.db.get_value("Purchase Order", self.purchase_order, "total")
			self.po_value = po_total or 0
