// Copyright (c) 2026, Connect 4 systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("Import Expense", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && ["Approved", "Allocated"].includes(frm.doc.expense_status)
			&& frm.doc.payment_status !== "Paid") {
			frm.add_custom_button(__("Create Payment"), () => open_expense_payment(frm), __("Actions"));
		}
		if (!frm.is_new()) render_expense_payments(frm);
	},
	setup(frm) {
		frm.set_query("import_shipment", function() {
			return {
				filters: {
					company: frm.doc.company || "",
					shipment_status: ["not in", ["Closed", "Cancelled"]]
				}
			};
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
		frm.set_value("expense_account", null);
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

async function open_expense_payment(frm) {
	const method = "c4agent.c4agent.services.expense_payment.";
	const initial = await frappe.call({method: method + "payment_details", args: {expense_name: frm.doc.name}});
	const request_id = crypto.randomUUID();
	let sequence = 0;
	let ready = true;
	let dialog;
	dialog = new frappe.ui.Dialog({
		title: __("Create Payment"),
		fields: [
			{fieldname: "payment_date", label: __("Payment Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1, onchange: () => refresh_details(false)},
			{fieldname: "mode_of_payment", label: __("Mode of Payment"), fieldtype: "Link", options: "Mode of Payment", reqd: 1,
				get_query: () => ({filters: {enabled: 1}}), onchange: () => refresh_details(true)},
			{fieldname: "payment_account", label: __("Payment Account"), fieldtype: "Link", options: "Account", reqd: 1,
				get_query: () => ({filters: {company: frm.doc.company, is_group: 0, disabled: 0, account_type: ["in", ["Bank", "Cash"]]}})},
			{fieldname: "currency", label: __("Currency"), fieldtype: "Link", options: "Currency", read_only: 1, default: initial.message.currency},
			{fieldname: "exchange_rate", label: __("Exchange Rate"), fieldtype: "Float", precision: 9, read_only: 1, default: initial.message.exchange_rate},
			{fieldname: "amount", label: __("Amount to Pay"), fieldtype: "Currency", options: "currency", reqd: 1, default: initial.message.amount},
			{fieldname: "maximum", label: __("Maximum Payable"), fieldtype: "Currency", options: "currency", read_only: 1, default: initial.message.amount}
		],
		primary_action_label: __("Create and Submit Payment"),
		async primary_action(values) {
			if (!ready) return;
			if (values.amount <= 0 || values.amount > dialog.get_value("maximum")) {
				frappe.msgprint(__("Enter a positive amount within the maximum payable balance."));
				return;
			}
			dialog.get_primary_btn().prop("disabled", true);
			try {
				const result = await frappe.call({method: method + "create_payment", freeze: true,
					args: {expense_name: frm.doc.name, payment_date: values.payment_date,
						mode_of_payment: values.mode_of_payment, payment_account: values.payment_account,
						amount: values.amount, request_id}});
				dialog.hide();
				await frm.reload_doc();
				frappe.msgprint(__("Payment Journal Entry created: {0}", [frappe.utils.get_form_link("Journal Entry", result.message, true)]));
			} finally {
				dialog.get_primary_btn().prop("disabled", false);
			}
		}
	});
	async function refresh_details(set_account) {
		if (!dialog) return;
		const current = ++sequence;
		ready = false;
		dialog.get_primary_btn().prop("disabled", true);
		try {
			const result = await frappe.call({method: method + "payment_details", args: {
				expense_name: frm.doc.name, payment_date: dialog.get_value("payment_date"), mode_of_payment: dialog.get_value("mode_of_payment")
			}});
			if (current !== sequence) return;
			await dialog.set_value("exchange_rate", result.message.exchange_rate);
			await dialog.set_value("maximum", result.message.amount);
			if (set_account) await dialog.set_value("payment_account", result.message.payment_account || "");
			if (dialog.get_value("amount") > result.message.amount) await dialog.set_value("amount", result.message.amount);
			ready = true;
		} finally {
			if (current === sequence) dialog.get_primary_btn().prop("disabled", !ready);
		}
	}
	dialog.show();
}

async function render_expense_payments(frm) {
	const result = await frappe.call({method: "c4agent.c4agent.services.expense_payment.payment_history", args: {expense_name: frm.doc.name}});
	const escape = frappe.utils.escape_html;
	const rows = (result.message || []).map(row => `<tr><td>${frappe.utils.get_form_link("Journal Entry", row.name, true)}</td><td>${escape(row.posting_date)}</td><td>${escape(row.mode_of_payment || "")}</td><td>${escape(row.custom_payment_currency || "")}</td><td>${escape(String(row.custom_payment_exchange_rate))}</td><td>${escape(String(row.custom_payment_amount))}</td><td>${escape(__(row.docstatus === 1 ? "Submitted" : row.docstatus === 2 ? "Cancelled" : "Draft"))}</td></tr>`).join("");
	frm.get_field("payment_history").$wrapper.html(rows ? `<table class="table table-bordered"><thead><tr>${["Journal Entry", "Date", "Mode of Payment", "Currency", "Exchange Rate", "Amount", "Status"].map(label => `<th>${escape(__(label))}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table>` : `<p class="text-muted">${__("No payments recorded.")}</p>`);
}
