frappe.ui.form.on("Import Expense Type", {
	setup(frm) {
		frm.set_query("default_expense_account", "company_accounts", (doc, cdt, cdn) => {
			const filters = {company: locals[cdt][cdn].company || "", is_group: 0, disabled: 0};
			return doc.is_recoverable_tax
				? {filters, or_filters: [["Account", "root_type", "in", ["Expense", "Asset"]], ["Account", "account_type", "=", "Tax"]]}
				: {filters: {...filters, root_type: "Expense"}};
		});
	}
});
frappe.ui.form.on("Import Expense Company Account", {
	company(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "default_expense_account", "");
	}
});
