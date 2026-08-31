// Copyright (c) 2026, Connect 4 systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
	refresh(frm) {
		// Add "Create Import Shipment" button if PO is submitted
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Import Shipment"), function() {
				frappe.call({
					method: "c4agent.c4agent.services.shipment.create_import_shipment_from_po",
					args: {
						po_name: frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							frappe.show_alert({
								message: __("Import Shipment created: {0}", [r.message]),
								indicator: "green"
							});
							// Optionally open the new shipment
							frappe.set_route("Form", "Import Shipment", r.message);
						}
					}
				});
			}, __("Create"));
		}
	}
});
