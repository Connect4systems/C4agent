// Copyright (c) 2026, Connect 4 systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Receipt", {
	setup(frm) {
		frm.set_query("custom_import_container", "items", function() {
			return {
				filters: {
					import_shipment: frm.doc.custom_import_shipment || ""
				}
			};
		});
	},

	custom_import_shipment(frm) {
		for (const row of frm.doc.items || []) {
			frappe.model.set_value(row.doctype, row.name, "custom_import_container", null);
		}
	}
});
