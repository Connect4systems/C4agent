frappe.ui.form.on("Purchase Invoice", {
	refresh(frm) {
		frm.set_query("custom_import_shipment", () => ({filters:{company:frm.doc.company, supplier:frm.doc.supplier}}));
	},
});
