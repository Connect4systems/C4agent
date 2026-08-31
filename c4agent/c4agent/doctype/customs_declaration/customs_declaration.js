frappe.ui.form.on("Customs Declaration", {
	refresh(frm) {
		frm.set_query("import_shipment", () => ({ filters: { company: frm.doc.company } }));
		frm.set_query("customs_broker", () => ({ filters: { custom_is_customs_broker: 1 } }));
	},
});
