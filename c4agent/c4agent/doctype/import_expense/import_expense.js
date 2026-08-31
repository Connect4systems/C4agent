// Copyright (c) 2026, Connect 4 systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("Import Expense", {
	setup(frm) {
		frm.set_query("import_shipment", function() {
			return {
				filters: {
					company: frm.doc.company || "",
					shipment_status: ["not in", ["Closed", "Cancelled"]]
				}
			};
		});

		frm.set_query("import_container", function() {
			return {filters: {import_shipment: frm.doc.import_shipment || ""}};
		});

		frm.set_query("expense_type", function() {
			return {filters: {disabled: 0}};
		});

		frm.set_query("expense_account", function() {
			return {filters: {company: frm.doc.company || "", is_group: 0}};
		});

		frm.set_query("supplier_invoice", function() {
			const filters = {company: frm.doc.company || "", docstatus: 1};
			if (frm.doc.supplier) filters.supplier = frm.doc.supplier;
			return {filters};
		});

		frm.set_query("accounting_reference_doctype", function() {
			return {filters: {name: ["in", ["Purchase Invoice", "Journal Entry", "Payment Entry"]]}};
		});
	},

	company(frm) {
		frm.set_value("import_shipment", null);
		frm.set_value("import_container", null);
		frm.set_value("expense_account", null);
	},

	import_shipment(frm) {
		frm.set_value("import_container", null);
	},

	async expense_type(frm) {
		if (!frm.doc.expense_type) return;
		const result = await frappe.db.get_value(
			"Import Expense Type",
			frm.doc.expense_type,
			["default_expense_account", "include_in_landed_cost", "is_recoverable_tax", "allocation_basis"]
		);
		const values = result.message || {};
		if (values.default_expense_account) {
			await frm.set_value("expense_account", values.default_expense_account);
		}
		await frm.set_value(
			"include_in_landed_cost",
			values.is_recoverable_tax ? 0 : values.include_in_landed_cost
		);
		await frm.set_value("allocation_basis", values.allocation_basis || "Amount");
	}
});
