frappe.ui.form.on("Sinosure Coverage", {
	refresh(frm) {
		frm.set_query("import_shipment", () => ({filters:{company:frm.doc.company, supplier:frm.doc.supplier}}));
	},
});
