frappe.ui.form.on("Import Shipment", {
	currency: update_commercial_exchange_rate,
	company_currency: update_commercial_exchange_rate,
	commercial_invoice_date: update_commercial_exchange_rate,
	async company(frm) {
		const result = frm.doc.company
			? await frappe.db.get_value("Company", frm.doc.company, "default_currency")
			: null;
		await frm.set_value("company_currency", result?.message?.default_currency || "");
	},
	before_workflow_action(frm) {
		if (frm.selected_workflow_action !== "Confirm Booking") return;
		return collect_booking_details(frm);
	},
	refresh(frm) {
		frm.set_query("purchase_order", () => ({ filters: { docstatus: 1, company: frm.doc.company, supplier: frm.doc.supplier } }));
		frm.set_query("sinosure_coverage", () => ({ filters: { company: frm.doc.company, supplier: frm.doc.supplier, coverage_status: "Active" } }));
		if (!frm.is_new()) {
			const actions = [
				["Import Expense", "Import Expense", {import_shipment:frm.doc.name, company:frm.doc.company}],
				["Sinosure Coverage", "Sinosure Coverage", {import_shipment:frm.doc.name, company:frm.doc.company, supplier:frm.doc.supplier}],
			];
			actions.forEach(([label, doctype, defaults]) => {
				frm.add_custom_button(__(label), () => frappe.new_doc(doctype, defaults), __("Create"));
			});
		}
		if (!frm.is_new() && ["Cleared", "Received"].includes(frm.doc.shipment_status)) {
			frm.add_custom_button(__("Purchase Receipt"), () => {
				frappe.model.open_mapped_doc({
					method: "c4agent.c4agent.services.shipment_receipt.make_purchase_receipt",
					frm: frm
				});
			}, __("Create"));
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

function collect_booking_details(frm) {
	return new Promise((resolve) => {
		const dialog = new frappe.ui.Dialog({
			title: __("Confirm Booking"),
			fields: [
				{
					fieldname: "shipping_line", label: __("Shipping Line"), fieldtype: "Link",
					options: "Shipping Line", reqd: 1, default: frm.doc.shipping_line,
					get_query: () => ({ filters: { disabled: 0 } }),
				},
				{ fieldname: "bill_of_lading", label: __("Bill of Lading"), fieldtype: "Data", reqd: 1, default: frm.doc.bill_of_lading },
				{ fieldname: "etd", label: __("ETD (Expected Departure Date)"), fieldtype: "Date", reqd: 1, default: frm.doc.etd },
				{ fieldname: "eta", label: __("ETA (Expected Arrival Date)"), fieldtype: "Date", reqd: 1, default: frm.doc.eta },
			],
			primary_action_label: __("Confirm Booking"),
			primary_action: async (values) => {
				if (values.eta < values.etd) {
					frappe.msgprint(__("ETA cannot be before ETD."));
					return;
				}
				await frm.set_value(values);
				dialog.hide();
				resolve();
			},
		});
		dialog.show();
	});
}

async function update_commercial_exchange_rate(frm) {
	const {currency, company_currency, commercial_invoice_date} = frm.doc;
	const request = (frm._commercial_rate_request || 0) + 1;
	frm._commercial_rate_request = request;
	await frm.set_value("exchange_rate", 0);
	if (!currency || !company_currency) return;
	if (currency === company_currency) {
		await frm.set_value("exchange_rate", 1);
		return;
	}
	const result = await frappe.call({
		method: "erpnext.setup.utils.get_exchange_rate",
		args: {from_currency: currency, to_currency: company_currency,
			transaction_date: commercial_invoice_date || frappe.datetime.get_today(), args: "for_buying"}
	});
	if (frm._commercial_rate_request !== request) return;
	await frm.set_value("exchange_rate", result.message || 0);
	if (!result.message) {
		frappe.msgprint(__("No exchange rate found. Add a Currency Exchange record or enter the Exchange Rate manually."));
	}
}
