import frappe
from frappe.tests.utils import FrappeTestCase


class TestC4agentReleaseContracts(FrappeTestCase):
	def test_all_phase_doctypes_are_installed(self):
		for doctype in (
			"Import Shipment",
			"Import Expense Type", "Import Expense", "Sinosure Coverage",
		):
			self.assertTrue(frappe.db.exists("DocType", doctype), doctype)

	def test_all_operational_workflows_are_active(self):
		for name, doctype in (
			("Import Shipment Lifecycle", "Import Shipment"),
			("Import Expense Approval", "Import Expense"),
			("Sinosure Coverage Lifecycle", "Sinosure Coverage"),
		):
			self.assertTrue(frappe.db.exists("Workflow", {
				"workflow_name": name, "document_type": doctype, "is_active": 1,
			}))

	def test_customs_clearance_is_part_of_the_shipment_workflow(self):
		workflow = frappe.get_doc("Workflow", "Import Shipment Lifecycle")
		transitions = {
			(row.state, row.action, row.next_state, row.allowed)
			for row in workflow.transitions
		}
		self.assertTrue(frappe.db.exists("DocType", "Import Shipment"))
		self.assertFalse(frappe.db.exists("DocType", "Customs Declaration"))
		self.assertTrue({
			("Under Customs Clearance", "Submit Documents", "Documents Submitted", "Customs User"),
			("Documents Submitted", "Start Review", "Under Review", "Customs User"),
			("Under Review", "Start Inspection", "Under Inspection", "Customs User"),
			("Under Review", "Assess Duties", "Duties Assessed", "Customs Manager"),
			("Under Inspection", "Assess Duties", "Duties Assessed", "Customs Manager"),
			("Duties Assessed", "Release Shipment", "Cleared", "Customs Manager"),
		}.issubset(transitions))
		self.assertFalse(any(row.action in {"Request Payment", "Confirm Payment"} for row in workflow.transitions))

	def test_standard_erpnext_integration_fields_exist(self):
		for doctype, fieldname in (
			("Purchase Invoice", "custom_import_shipment"),
			("Purchase Invoice", "custom_acid_issue_date"),
			("Purchase Invoice", "custom_sinosure_reference"),
			("Purchase Receipt", "custom_import_shipment"),
			("Landed Cost Voucher", "custom_import_shipment"),
			("Landed Cost Taxes and Charges", "custom_import_expense"),
			("Supplier", "custom_is_foreign_supplier"),
			("Item", "custom_wattage"),
		):
			self.assertTrue(frappe.get_meta(doctype).has_field(fieldname), f"{doctype}.{fieldname}")

	def test_release_reports_exist(self):
		for report in ("Import Pipeline", "Shipment Cost Summary", "Sinosure Exposure"):
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
		for link in workspace.links:
			if link.type != "Link":
				continue
			self.assertTrue(link.link_type, f"Link Type is missing for {link.label}")
			self.assertTrue(link.link_to, f"Link To is missing for {link.label}")
