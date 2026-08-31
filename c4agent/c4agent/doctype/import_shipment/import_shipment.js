frappe.ui.form.on("Import Shipment", {
	refresh(frm) {
		frm.set_query("purchase_order", () => ({ filters: { docstatus: 1, company: frm.doc.company, supplier: frm.doc.supplier } }));
		frm.set_query("sinosure_coverage", () => ({ filters: { company: frm.doc.company, supplier: frm.doc.supplier, coverage_status: "Active" } }));
		if (!frm.is_new()) {
			const actions = [
				["Import Container", "Import Container", {import_shipment:frm.doc.name}],
				["Customs Declaration", "Customs Declaration", {import_shipment:frm.doc.name, company:frm.doc.company}],
				["Import Expense", "Import Expense", {import_shipment:frm.doc.name, company:frm.doc.company}],
				["Sinosure Coverage", "Sinosure Coverage", {import_shipment:frm.doc.name, company:frm.doc.company, supplier:frm.doc.supplier}],
			];
			actions.forEach(([label, doctype, defaults]) => {
				frm.add_custom_button(__(label), () => frappe.new_doc(doctype, defaults), __("Create"));
			});
		}
		if (!frm.is_new() && ["Cleared", "Received"].includes(frm.doc.shipment_status)) {
			frm.add_custom_button(__("Create Landed Cost Vouchers"), () => {
				frappe.call({
					method: "c4agent.c4agent.services.costing.make_landed_cost_vouchers",
					args: { import_shipment: frm.doc.name },
					freeze: true,
					callback: (r) => frappe.msgprint(__("Created draft vouchers: {0}", [(r.message || []).join(", ")]))
				});
			}, __("Create"));
		}
		if (frm.doc.shipment_status === "Closed") {
			frm.add_custom_button(__("Reopen Shipment"), () => {
				frappe.prompt({fieldname:"reason", fieldtype:"Small Text", label:__("Reopen Reason"), reqd:1}, (v) => {
					frappe.call({method:"c4agent.c4agent.services.shipment.reopen_import_shipment", args:{shipment:frm.doc.name, reason:v.reason}, callback:() => frm.reload_doc()});
				}, __("Reopen Shipment"));
			});
		}
	},
});
