frappe.ui.form.on("Purchase Invoice", {
	refresh(frm) {
		frm.set_query("custom_import_shipment", () => ({filters:{company:frm.doc.company, supplier:frm.doc.supplier}}));
		frm.set_query("import_container", "custom_import_containers", () => ({filters:{import_shipment:frm.doc.custom_import_shipment}}));
	},
});

frappe.ui.form.on("Purchase Invoice Import Container", {
	import_container(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.import_container) return;
		frappe.db.get_value("Import Container", row.import_container, "import_shipment").then((r) => {
			if (r.message.import_shipment !== frm.doc.custom_import_shipment) {
				frappe.model.set_value(cdt, cdn, "import_container", null);
				frappe.throw(__("Container must belong to the selected Import Shipment"));
			}
		});
	},
});
