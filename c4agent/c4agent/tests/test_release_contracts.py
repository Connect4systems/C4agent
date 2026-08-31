import frappe
from frappe.tests.utils import FrappeTestCase


class TestC4agentReleaseContracts(FrappeTestCase):
	def test_all_phase_doctypes_are_installed(self):
		for doctype in (
			"Import Shipment", "Import Container", "Customs Declaration",
			"Import Expense Type", "Import Expense", "Sinosure Coverage",
		):
			self.assertTrue(frappe.db.exists("DocType", doctype), doctype)

	def test_all_operational_workflows_are_active(self):
		for name, doctype in (
			("Import Shipment Lifecycle", "Import Shipment"),
			("Customs Declaration Lifecycle", "Customs Declaration"),
			("Import Expense Approval", "Import Expense"),
			("Sinosure Coverage Lifecycle", "Sinosure Coverage"),
		):
			self.assertTrue(frappe.db.exists("Workflow", {
				"workflow_name": name, "document_type": doctype, "is_active": 1,
			}))

	def test_standard_erpnext_integration_fields_exist(self):
		for doctype, fieldname in (
			("Purchase Invoice", "custom_import_shipment"),
			("Purchase Invoice", "custom_import_containers"),
			("Purchase Invoice", "custom_acid_issue_date"),
			("Purchase Invoice", "custom_sinosure_reference"),
			("Purchase Receipt", "custom_import_shipment"),
			("Purchase Receipt Item", "custom_import_container"),
			("Landed Cost Voucher", "custom_import_shipment"),
			("Landed Cost Taxes and Charges", "custom_import_expense"),
			("Supplier", "custom_is_foreign_supplier"),
			("Item", "custom_wattage"),
		):
			self.assertTrue(frappe.get_meta(doctype).has_field(fieldname), f"{doctype}.{fieldname}")

	def test_release_reports_exist(self):
		for report in ("Import Pipeline", "Shipment Cost Summary", "Container Cost Summary", "Sinosure Exposure"):
			self.assertTrue(frappe.db.exists("Report", report), report)

	def test_recoverable_vat_policy_is_seeded_safely(self):
		vat = frappe.db.get_value("Import Expense Type", "Import VAT", ["include_in_landed_cost", "is_recoverable_tax"], as_dict=True)
		self.assertIsNotNone(vat)
		self.assertEqual(vat.include_in_landed_cost, 0)
		self.assertEqual(vat.is_recoverable_tax, 1)

	def test_import_shipment_dashboard_has_one_valid_mapping_per_item(self):
		data = frappe.get_meta("Import Shipment").get_dashboard_data()
		items = [item for group in data.transactions for item in group.get("items", [])]
		self.assertEqual(len(items), len(set(items)))
		for doctype in items:
			fieldname = data.get("non_standard_fieldnames", {}).get(doctype) or data.get("fieldname")
			self.assertTrue(fieldname, f"Dashboard field mapping is missing for {doctype}")

	def test_c4agent_workspace_has_renderable_content(self):
		workspace = frappe.get_doc("Workspace", "C4agent")
		self.assertEqual(workspace.title, "C4agent")
		self.assertTrue(workspace.content)
		blocks = frappe.parse_json(workspace.content)
		self.assertIsInstance(blocks, list)
		self.assertTrue(blocks)
		self.assertEqual(len([block for block in blocks if block.get("type") == "card"]), 5)
