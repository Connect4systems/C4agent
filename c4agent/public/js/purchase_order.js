// Copyright (c) 2026, Connect 4 systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
	refresh(frm) {
		// Add "Create Import Shipment" button if PO is submitted
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Import Shipment"), function() {
				frappe.model.open_mapped_doc({
					method: "c4agent.c4agent.services.shipment.make_import_shipment",
					frm: frm
				});
			}, __("Create"));
		}
	}
});
