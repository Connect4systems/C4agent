# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

from datetime import datetime, timedelta

import frappe
from frappe.tests.utils import FrappeTestCase

from c4agent.c4agent.services.shipment import make_import_shipment


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
			"shipment_id": "TEST-SHIP-" + frappe.generate_hash(length=10),
			"company": self.company,
			"supplier": self.supplier,
			"purchase_order": po,
			"shipping_line": self.shipping_line,
			"port_of_loading": "Shanghai",
			"port_of_discharge": "Alexandria"
		})
		
		shipment.insert()
		self.assertEqual(shipment.name, shipment.shipment_id)
		self.assertEqual(shipment.shipment_status, "Draft")
		self.assertIsNotNone(shipment.shipment_title)

	def test_map_purchase_order_to_unsaved_import_shipment(self):
		"""The PO action must open a populated draft without inserting it."""
		po = self.create_test_po()

		shipment = make_import_shipment(po)

		self.assertTrue(shipment.is_new())
		self.assertEqual(shipment.purchase_order, po)
		self.assertEqual(shipment.supplier, self.supplier)
		self.assertEqual(len(shipment.items), 1)
		self.assertEqual(shipment.items[0].ordered_qty, 100)
	
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
			"shipment_id": "TEST-SHIP-" + frappe.generate_hash(length=10),
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
			"shipment_id": "TEST-SHIP-" + frappe.generate_hash(length=10),
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
			"shipment_id": "TEST-SHIP-" + frappe.generate_hash(length=10),
			"company": self.company,
			"supplier": self.supplier,
			"purchase_order": po,
			"etd": etd,
			"eta": eta
		})
		
		self.assertRaises(Exception, shipment.insert)
	
	def test_manual_container_count_survives_save(self):
		shipment = make_import_shipment(self.create_test_po())
		shipment.shipment_id = "TEST-SHIP-" + frappe.generate_hash(length=10)
		shipment.container_count = 3
		shipment.insert()
		shipment.container_count = 5
		shipment.save()
		shipment.reload()
		self.assertEqual(shipment.container_count, 5)


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


class TestC4agentSetup(FrappeTestCase):
	"""Verify app-owned setup records created by install or migrate."""

	def test_roles_and_shipment_workflow_exist(self):
		for role in (
			"Import User",
			"Import Manager",
			"Customs User",
			"Customs Manager",
			"Finance User",
			"Finance Manager",
		):
			self.assertTrue(frappe.db.exists("Role", role))

		self.assertTrue(
			frappe.db.exists(
				"Workflow",
				{
					"workflow_name": "Import Shipment Lifecycle",
					"document_type": "Import Shipment",
					"is_active": 1,
				},
			)
		)
