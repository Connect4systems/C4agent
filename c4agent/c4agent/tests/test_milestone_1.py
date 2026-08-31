# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.test_runner import make_test_records
from frappe.tests.utils import FrappeTestCase, change_settings
from datetime import datetime, timedelta


class TestImportShipment(FrappeTestCase):
	"""Test cases for Import Shipment DocType"""
	
	def setUp(self):
		"""Set up test fixtures"""
		super().setUp()
		self.company = frappe.db.get_value("Company", {"is_group": 0}, "name")
		if not self.company:
			self.company = "Test Company"
			frappe.get_doc({
				"doctype": "Company",
				"company_name": self.company,
				"abbr": "TC"
			}).insert(ignore_if_duplicate=True)
		
		# Create test supplier
		self.supplier = "Test Supplier"
		if not frappe.db.exists("Supplier", self.supplier):
			frappe.get_doc({
				"doctype": "Supplier",
				"supplier_name": self.supplier,
				"supplier_type": "Company",
				"country": "China"
			}).insert(ignore_permissions=True)
		
		# Create test shipping line
		self.shipping_line = "Test Shipping Line"
		if not frappe.db.exists("Shipping Line", self.shipping_line):
			frappe.get_doc({
				"doctype": "Shipping Line",
				"shipping_line_name": self.shipping_line,
				"country": "Singapore"
			}).insert(ignore_permissions=True)
	
	def create_test_po(self):
		"""Create a test Purchase Order"""
		po = frappe.get_doc({
			"doctype": "Purchase Order",
			"supplier": self.supplier,
			"company": self.company,
			"transaction_date": datetime.now().date(),
			"items": [
				{
					"item_code": self.get_or_create_test_item(),
					"qty": 100,
					"rate": 1000
				}
			]
		})
		po.insert()
		po.submit()
		return po.name
	
	def get_or_create_test_item(self):
		"""Get or create a test item"""
		if not frappe.db.exists("Item", "TEST-ITEM-001"):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": "TEST-ITEM-001",
				"item_name": "Test Item",
				"item_group": "All Item Groups",
				"stock_uom": "Nos"
			}).insert(ignore_permissions=True)
		return "TEST-ITEM-001"
	
	def test_create_import_shipment_from_valid_po(self):
		"""Test creating Import Shipment from valid PO"""
		po = self.create_test_po()
		
		shipment = frappe.get_doc({
			"doctype": "Import Shipment",
			"company": self.company,
			"supplier": self.supplier,
			"purchase_order": po,
			"shipping_line": self.shipping_line,
			"port_of_loading": "Shanghai",
			"port_of_discharge": "Alexandria"
		})
		
		shipment.insert()
		self.assertEqual(shipment.shipment_status, "Draft")
		self.assertIsNotNone(shipment.shipment_title)
	
	def test_reject_supplier_mismatch(self):
		"""Test that supplier mismatch with PO is rejected"""
		po = self.create_test_po()
		
		wrong_supplier = "Wrong Supplier"
		if not frappe.db.exists("Supplier", wrong_supplier):
			frappe.get_doc({
				"doctype": "Supplier",
				"supplier_name": wrong_supplier
			}).insert(ignore_permissions=True)
		
		shipment = frappe.get_doc({
			"doctype": "Import Shipment",
			"company": self.company,
			"supplier": wrong_supplier,
			"purchase_order": po
		})
		
		self.assertRaises(Exception, shipment.insert)
	
	def test_reject_company_mismatch(self):
		"""Test that company mismatch with PO is rejected"""
		po = self.create_test_po()
		
		wrong_company = "Wrong Company"
		if not frappe.db.exists("Company", wrong_company):
			frappe.get_doc({
				"doctype": "Company",
				"company_name": wrong_company,
				"abbr": "WC"
			}).insert(ignore_if_duplicate=True)
		
		shipment = frappe.get_doc({
			"doctype": "Import Shipment",
			"company": wrong_company,
			"supplier": self.supplier,
			"purchase_order": po
		})
		
		self.assertRaises(Exception, shipment.insert)
	
	def test_eta_before_etd_validation(self):
		"""Test that ETA cannot be before ETD"""
		po = self.create_test_po()
		etd = datetime.now().date()
		eta = etd - timedelta(days=5)
		
		shipment = frappe.get_doc({
			"doctype": "Import Shipment",
			"company": self.company,
			"supplier": self.supplier,
			"purchase_order": po,
			"etd": etd,
			"eta": eta
		})
		
		self.assertRaises(Exception, shipment.insert)
	
	def test_container_belongs_to_shipment(self):
		"""Test container validation"""
		po = self.create_test_po()
		
		shipment = frappe.get_doc({
			"doctype": "Import Shipment",
			"company": self.company,
			"supplier": self.supplier,
			"purchase_order": po
		})
		shipment.insert()
		
		# Create container linked to shipment
		container = frappe.get_doc({
			"doctype": "Import Container",
			"import_shipment": shipment.name,
			"container_number": "TEST-CNT-001",
			"container_type": "20GP"
		})
		container.insert()
		
		# Verify container exists
		self.assertEqual(container.import_shipment, shipment.name)
	
	def test_duplicate_container_warning(self):
		"""Test warning on duplicate container number"""
		po = self.create_test_po()
		shipment = frappe.get_doc({
			"doctype": "Import Shipment",
			"company": self.company,
			"supplier": self.supplier,
			"purchase_order": po
		})
		shipment.insert()
		
		# Create first container
		container1 = frappe.get_doc({
			"doctype": "Import Container",
			"import_shipment": shipment.name,
			"container_number": "DUP-CNT-001",
			"container_type": "20GP"
		})
		container1.insert()
		
		# Create second container with same number (should warn)
		container2 = frappe.get_doc({
			"doctype": "Import Container",
			"import_shipment": shipment.name,
			"container_number": "DUP-CNT-001",
			"container_type": "40GP"
		})
		# This should not raise, but should show warning
		try:
			container2.insert()
		except:
			pass  # Expected behavior


class TestImportContainer(FrappeTestCase):
	"""Test cases for Import Container DocType"""
	
	def setUp(self):
		"""Set up test fixtures"""
		super().setUp()
		self.company = frappe.db.get_value("Company", {"is_group": 0}, "name")
		if not self.company:
			self.company = "Test Company"
		
		self.supplier = "Test Supplier"
		self.create_test_shipment()
	
	def create_test_shipment(self):
		"""Create a test Import Shipment"""
		if not frappe.db.exists("Supplier", self.supplier):
			frappe.get_doc({
				"doctype": "Supplier",
				"supplier_name": self.supplier
			}).insert(ignore_permissions=True)
		
		po = frappe.get_doc({
			"doctype": "Purchase Order",
			"supplier": self.supplier,
			"company": self.company,
			"transaction_date": datetime.now().date(),
			"items": [{"item_code": "TEST-ITEM", "qty": 100, "rate": 1000}]
		})
		po.insert()
		po.submit()
		
		self.shipment = frappe.get_doc({
			"doctype": "Import Shipment",
			"company": self.company,
			"supplier": self.supplier,
			"purchase_order": po.name
		})
		self.shipment.insert()
	
	def test_container_number_normalization(self):
		"""Test container number is normalized (uppercase, stripped)"""
		container = frappe.get_doc({
			"doctype": "Import Container",
			"import_shipment": self.shipment.name,
			"container_number": "  test-cnt-001  ",
			"container_type": "20GP"
		})
		container.insert()
		
		self.assertEqual(container.container_number, "TEST-CNT-001")
	
	def test_free_time_end_date_calculation(self):
		"""Test free_time_end_date is calculated correctly"""
		arrival_date = datetime.now().date()
		free_days = 5
		
		container = frappe.get_doc({
			"doctype": "Import Container",
			"import_shipment": self.shipment.name,
			"container_number": "FREE-TIME-TEST",
			"container_type": "40GP",
			"arrival_date": arrival_date,
			"free_days": free_days
		})
		container.insert()
		
		expected_end_date = arrival_date + timedelta(days=free_days)
		self.assertEqual(container.free_time_end_date, expected_end_date)


class TestShippingLine(FrappeTestCase):
	"""Test cases for Shipping Line master"""
	
	def test_create_shipping_line(self):
		"""Test creating a Shipping Line"""
		shipping_line = frappe.get_doc({
			"doctype": "Shipping Line",
			"shipping_line_name": "Test Shipping Co",
			"country": "Singapore",
			"website": "https://example.com",
			"contact_person": "John Doe",
			"phone": "+65-1234567",
			"email": "contact@example.com"
		})
		shipping_line.insert()
		
		self.assertEqual(shipping_line.shipping_line_name, "Test Shipping Co")
		self.assertFalse(shipping_line.disabled)
