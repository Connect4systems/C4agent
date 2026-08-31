import frappe


@frappe.whitelist()
def make_landed_cost_vouchers(import_shipment):
	"""Create draft ERPNext LCVs grouped by its supported Amount/Qty bases."""
	frappe.has_permission("Landed Cost Voucher", "create", throw=True)
	shipment = frappe.get_doc("Import Shipment", import_shipment)
	company_currency = shipment.company_currency or frappe.db.get_value("Company", shipment.company, "default_currency")
	receipts = frappe.get_all("Purchase Receipt", filters={
		"custom_import_shipment": shipment.name, "docstatus": 1,
	}, fields=["name", "supplier", "posting_date", "grand_total"])
	if not receipts:
		frappe.throw("Submit at least one Purchase Receipt for this shipment first")
	if not frappe.db.exists("Customs Declaration", {"import_shipment": shipment.name, "clearance_status": "Released"}):
		frappe.msgprint("Customs Declaration is not Released; Finance Manager should review before submitting the voucher", indicator="orange", alert=True)
	expenses = frappe.get_all("Import Expense", filters={
		"import_shipment": shipment.name, "docstatus": 1, "include_in_landed_cost": 1,
		"landed_cost_allocated": 0,
	}, fields=["name", "expense_type", "expense_account", "currency", "amount", "exchange_rate", "base_amount", "allocation_basis", "landed_cost_exclusion_reason"])
	expenses = [e for e in expenses if not e.landed_cost_exclusion_reason]
	if not expenses:
		frappe.throw("There are no approved, unallocated landed-cost expenses")
	unsupported = [e.name for e in expenses if e.allocation_basis not in ("Amount", "Quantity")]
	if unsupported:
		frappe.msgprint("Create a manual ERPNext Landed Cost Voucher for Weight, Volume, or Manual expenses: " + ", ".join(unsupported), indicator="orange")
	if len(unsupported) == len(expenses):
		frappe.throw("All eligible expenses require manual Weight, Volume, or Manual allocation")

	created = []
	for basis in ("Amount", "Quantity"):
		group = [e for e in expenses if e.allocation_basis == basis]
		if not group:
			continue
		lcv = frappe.new_doc("Landed Cost Voucher")
		lcv.company = shipment.company
		lcv.custom_import_shipment = shipment.name
		lcv.distribute_charges_based_on = "Qty" if basis == "Quantity" else "Amount"
		for receipt in receipts:
			lcv.append("purchase_receipts", {
				"receipt_document_type": "Purchase Receipt", "receipt_document": receipt.name,
				"supplier": receipt.supplier, "posting_date": receipt.posting_date,
				"grand_total": receipt.grand_total,
			})
		lcv.get_items_from_purchase_receipts()
		for expense in group:
			account_currency = frappe.db.get_value("Account", expense.expense_account, "account_currency") or company_currency
			if account_currency == expense.currency:
				amount, exchange_rate = expense.amount, expense.exchange_rate
			elif account_currency == company_currency:
				amount, exchange_rate = expense.base_amount, 1
			else:
				frappe.throw(f"Expense {expense.name}: account currency {account_currency} is incompatible with transaction currency {expense.currency}")
			lcv.append("taxes", {
				"expense_account": expense.expense_account, "description": f"{expense.expense_type} / {expense.name}",
				"amount": amount, "account_currency": account_currency,
				"exchange_rate": exchange_rate, "base_amount": expense.base_amount,
				"custom_import_expense": expense.name,
			})
		lcv.insert()
		created.append(lcv.name)
	return created


@frappe.whitelist()
def make_landed_cost_voucher(import_shipment):
	"""Compatibility endpoint named in the implementation brief."""
	return make_landed_cost_vouchers(import_shipment)
