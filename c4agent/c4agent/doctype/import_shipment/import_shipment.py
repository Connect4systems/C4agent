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
		self.validate_shipment_items()
		self.validate_eta_after_etd()
		self.validate_sinosure_coverage()
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

	def validate_shipment_items(self):
		if not self.purchase_order:
			return
		po_items = {row.name: row for row in frappe.get_doc("Purchase Order", self.purchase_order).items}
		for row in self.items:
			po_row = po_items.get(row.purchase_order_item)
			if not po_row or po_row.item_code != row.item_code:
				frappe.throw(f"Row {row.idx}: item must reference a row from Purchase Order {self.purchase_order}")
			if (row.shipped_qty or 0) < 0:
				frappe.throw(f"Row {row.idx}: Shipped Qty cannot be negative")
			other_qty = frappe.db.sql("""select coalesce(sum(i.shipped_qty),0)
				from `tabImport Shipment Item` i inner join `tabImport Shipment` s on s.name=i.parent
				where i.purchase_order_item=%s and s.name!=%s and s.shipment_status!='Cancelled'""",
				(row.purchase_order_item, self.name or ""))[0][0]
			if (other_qty or 0) + (row.shipped_qty or 0) > po_row.qty:
				frappe.throw(f"Row {row.idx}: total shipped quantity across shipments exceeds PO quantity {po_row.qty}")
			row.ordered_qty = po_row.qty
			row.item_name = po_row.item_name
			row.uom = po_row.uom
			row.rate = po_row.rate
			row.amount = (row.shipped_qty or 0) * (row.rate or 0)
			row.total_watts = (row.shipped_qty or 0) * (row.wattage or 0)
	
	def validate_eta_after_etd(self):
		"""Validate ETA is not before ETD"""
		if self.etd and self.eta and self.eta < self.etd:
			frappe.throw("ETA cannot be before ETD")
		if self.actual_departure_date and self.actual_arrival_date and self.actual_arrival_date < self.actual_departure_date:
			frappe.throw("Actual Arrival Date cannot be before Actual Departure Date")

	def validate_sinosure_coverage(self):
		if not self.sinosure_coverage:
			return
		coverage = frappe.get_doc("Sinosure Coverage", self.sinosure_coverage)
		if coverage.company != self.company or coverage.supplier != self.supplier:
			frappe.throw("Sinosure Coverage must belong to the shipment company and supplier")
		if coverage.coverage_status in ("Expired", "Closed", "Rejected") and self.shipment_status not in ("Closed", "Cancelled"):
			frappe.msgprint(f"Sinosure Coverage is {coverage.coverage_status}; Finance should review the open exposure", indicator="orange", alert=True)
		if self.supplier_currency and coverage.coverage_currency != self.supplier_currency:
			frappe.throw("Sinosure Coverage currency must match the shipment supplier currency")
		if coverage.import_shipment != self.name:
			frappe.throw("Sinosure Coverage must reference this Import Shipment")
	
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
		if frappe.db.exists("DocType", "Customs Declaration") and frappe.db.exists(
			"Customs Declaration", {"import_shipment": self.name, "clearance_status": "Released"}
		):
			frappe.throw("Resolve the Released Customs Declaration before cancelling this shipment")

	def validate_basic_closure(self):
		"""Require physical receipt, customs release, and complete cost allocation."""
		manager_roles = {"Import Manager", "Finance Manager", "System Manager"}
		if self.close_override_reason and not (manager_roles & set(frappe.get_roles())):
			frappe.throw("Only Import Manager, Finance Manager, or System Manager can use a closure override")
		if not frappe.db.exists(
			"Purchase Receipt",
			{"custom_import_shipment": self.name, "docstatus": 1},
		):
			frappe.throw("At least one submitted Purchase Receipt is required before closing")

		if (
			frappe.db.exists("DocType", "Customs Declaration")
			and not frappe.db.exists(
				"Customs Declaration", {"import_shipment": self.name, "clearance_status": "Released"}
			)
			and not self.close_override_reason
		):
			frappe.throw("A Released Customs Declaration is required before closing")

		if frappe.db.exists("DocType", "Import Expense"):
			pending = frappe.db.count("Import Expense", {"import_shipment": self.name, "docstatus": 0})
			unallocated = frappe.db.sql("""select count(*) from `tabImport Expense`
				where import_shipment=%s and docstatus=1 and include_in_landed_cost=1
				and landed_cost_allocated=0 and coalesce(landed_cost_exclusion_reason, '')=''""", (self.name,))[0][0]
			if (pending or unallocated) and not self.close_override_reason:
				frappe.throw(f"Cannot close: {pending} pending and {unallocated} unallocated import expenses")

		missing = [label for field, label in (
			("acid_number", "ACID Number"), ("bill_of_lading", "Bill of Lading"),
			("actual_departure_date", "Actual Departure Date"),
			("actual_arrival_date", "Actual Arrival Date"),
			("customs_clearance_date", "Customs Clearance Date"),
		) if not self.get(field)]
		if missing and not self.close_override_reason:
			frappe.throw("Complete required logistics information before closing: " + ", ".join(missing))

		settings = frappe.get_single("C4agent Settings")
		if (
			settings.require_landed_cost_before_closing
			and not frappe.db.exists(
				"Landed Cost Voucher",
				{"custom_import_shipment": self.name, "docstatus": 1},
			)
			and not self.close_override_reason
		):
			frappe.throw("A submitted Landed Cost Voucher is required before closing")

		expected_qty = sum(row.shipped_qty or 0 for row in self.items)
		received_qty = frappe.db.sql("""
			select coalesce(sum(pri.qty), 0)
			from `tabPurchase Receipt Item` pri
			inner join `tabPurchase Receipt` pr on pr.name=pri.parent
			where pr.custom_import_shipment=%s and pr.docstatus=1
		""", (self.name,))[0][0]
		if not settings.allow_partial_shipment_closure and received_qty < expected_qty and not self.close_override_reason:
			frappe.throw("Shipment is only partially received; enter a Close Override Reason if this is intentional")
	
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

		self.supplier_invoice_value = sum(row.base_total or 0 for row in frappe.get_all(
			"Purchase Invoice", filters={"custom_import_shipment": self.name, "docstatus": 1}, fields=["base_total"]
		)) if self.name else 0
		self.purchase_receipt_value = sum(row.base_total or 0 for row in frappe.get_all(
			"Purchase Receipt", filters={"custom_import_shipment": self.name, "docstatus": 1}, fields=["base_total"]
		)) if self.name else 0
		self.total_landed_cost = sum(row.total_taxes_and_charges or 0 for row in frappe.get_all(
			"Landed Cost Voucher", filters={"custom_import_shipment": self.name, "docstatus": 1}, fields=["total_taxes_and_charges"]
		)) if self.name else 0
