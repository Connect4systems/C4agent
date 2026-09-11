"""Approved expense payments posted through standard Journal Entries."""
import math
from decimal import Decimal, ROUND_DOWN

import frappe
from frappe.utils import flt, getdate, nowdate
from erpnext.setup.utils import get_exchange_rate


def setup_payment_fields():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	fields = []
	for name, label, kind, options in (
		('custom_import_expense', 'Import Expense', 'Link', 'Import Expense'),
		('custom_import_shipment', 'Import Shipment', 'Link', 'Import Shipment'),
		('custom_payment_currency', 'Expense Payment Currency', 'Link', 'Currency'),
		('custom_payment_amount', 'Expense Payment Amount', 'Currency', 'custom_payment_currency'),
		('custom_payment_exchange_rate', 'Expense Payment Exchange Rate', 'Float', None),
		('custom_payment_request', 'Expense Payment Request', 'Data', None),
	):
		fields.append(dict(fieldname=name, label=label, fieldtype=kind, options=options,
			read_only=1, no_copy=1, insert_after=fields[-1]['fieldname'] if fields else 'user_remark'))
	create_custom_fields({'Journal Entry': fields}, update=True)


def payment_totals(expense):
	rows = frappe.get_all('Journal Entry', filters={'custom_import_expense': expense.name, 'docstatus': 1},
		fields=['custom_payment_amount'])
	paid = flt(sum(flt(r.custom_payment_amount) for r in rows), expense.precision('amount'))
	return paid, max(0, flt(expense.amount - paid, expense.precision('amount')))


def rate(currency, company_currency, date):
	value = 1 if currency == company_currency else flt(get_exchange_rate(currency, company_currency, date, 'for_buying'))
	if not math.isfinite(value) or value <= 0:
		frappe.throw(f'No exchange rate for {currency} to {company_currency}. Add a Currency Exchange record.')
	return value


def approved_expense(name):
	expense = frappe.get_doc('Import Expense', name)
	expense.check_permission('write')
	if expense.docstatus != 1 or expense.expense_status not in ('Approved', 'Allocated'):
		frappe.throw('Only approved expenses can be paid')
	return expense


def invoice_for(expense):
	name = expense.supplier_invoice
	if expense.accounting_reference_name:
		if expense.accounting_reference_doctype != 'Purchase Invoice':
			frappe.throw('This expense already references an accounting transaction. Settle that transaction directly to avoid booking the expense twice.')
		if name and name != expense.accounting_reference_name:
			frappe.throw('Supplier Invoice and Accounting Reference must identify the same invoice')
		name = name or expense.accounting_reference_name
	if not name:
		return None
	invoice = frappe.get_doc('Purchase Invoice', name)
	invoice.check_permission('read')
	if invoice.docstatus != 1 or invoice.is_return or invoice.company != expense.company:
		frappe.throw('A submitted, non-return Supplier Invoice in the expense company is required')
	if expense.supplier and invoice.supplier != expense.supplier:
		frappe.throw('Supplier Invoice supplier does not match the expense')
	return invoice


def account_details(name, company):
	account = frappe.get_doc('Account', name)
	account.check_permission('read')
	if account.company != company or account.is_group or account.disabled:
		frappe.throw('Select an enabled ledger account in the expense company')
	return account


@frappe.whitelist()
def payment_details(expense_name, payment_date=None, mode_of_payment=None):
	expense = approved_expense(expense_name)
	date = getdate(payment_date or nowdate())
	base_currency = frappe.get_cached_value('Company', expense.company, 'default_currency')
	exchange_rate = rate(expense.currency, base_currency, date)
	paid, outstanding = payment_totals(expense)
	invoice = invoice_for(expense)
	maximum = outstanding
	if invoice:
		account = account_details(invoice.credit_to, expense.company)
		invoice_rate = rate(account.account_currency or base_currency, base_currency, date)
		maximum = min(maximum, max(0, flt(invoice.outstanding_amount)) * invoice_rate / exchange_rate)
	account = None
	if mode_of_payment:
		mode = frappe.get_doc('Mode of Payment', mode_of_payment)
		if not mode.enabled:
			frappe.throw('Mode of Payment is disabled')
		account = next((r.default_account for r in mode.accounts if r.company == expense.company), None)
	# Never round the invoice limit upward into an overpayment.
	maximum = float(Decimal(str(maximum)).quantize(
		Decimal(1).scaleb(-(expense.precision('amount') or 2)), rounding=ROUND_DOWN))
	return dict(currency=expense.currency, exchange_rate=exchange_rate, amount=maximum,
		total_paid=paid, outstanding_amount=outstanding, payment_account=account)


@frappe.whitelist()
def create_payment(expense_name, payment_date, mode_of_payment, payment_account, amount, request_id):
	if not request_id or len(request_id) > 140:
		frappe.throw('Payment request identifier is required')
	# Serialize partial payments and duplicate requests for this expense.
	frappe.db.get_value('Import Expense', expense_name, 'name', for_update=True)
	expense = approved_expense(expense_name)
	if not frappe.has_permission('Journal Entry', 'create') or not frappe.has_permission('Journal Entry', 'submit'):
		frappe.throw('Create and Submit permission on Journal Entry is required', frappe.PermissionError)
	existing = frappe.db.get_value('Journal Entry', {'custom_import_expense': expense.name, 'custom_payment_request': request_id}, ['name', 'docstatus'], as_dict=True)
	if existing:
		if existing.docstatus != 1:
			frappe.throw('This request was cancelled. Open Create Payment again.')
		return existing.name
	invoice = invoice_for(expense)
	if invoice:
		frappe.db.get_value('Purchase Invoice', invoice.name, 'name', for_update=True)
		invoice.reload()
	details = payment_details(expense_name, payment_date, mode_of_payment)
	amount = flt(amount, expense.precision('amount'))
	if not math.isfinite(amount) or amount <= 0 or amount > details['amount']:
		frappe.throw('Payment must be positive and cannot exceed the expense or invoice outstanding balance')
	if not mode_of_payment or not payment_date:
		frappe.throw('Payment Date and Mode of Payment are required')
	credit = account_details(payment_account, expense.company)
	if credit.account_type not in ('Bank', 'Cash'):
		frappe.throw('Payment Account must be a Bank or Cash account')
	debit = account_details(invoice.credit_to if invoice else expense.expense_account, expense.company)
	if not invoice and debit.account_type in ('Payable', 'Receivable'):
		frappe.throw('Select an Expense / Tax Account for an unbooked expense')
	if debit.name == credit.name:
		frappe.throw('Payment and debit accounts must be different')
	base_currency = frappe.get_cached_value('Company', expense.company, 'default_currency')
	base_amount = amount * details['exchange_rate']
	journal = frappe.new_doc('Journal Entry')
	journal.update(dict(company=expense.company, posting_date=payment_date, voucher_type='Journal Entry',
		mode_of_payment=mode_of_payment, multi_currency=1, custom_import_expense=expense.name,
		custom_import_shipment=expense.import_shipment, custom_payment_currency=expense.currency,
		custom_payment_amount=amount, custom_payment_exchange_rate=details['exchange_rate'], custom_payment_request=request_id,
		user_remark=f'Payment for Import Expense {expense.name}; Shipment {expense.import_shipment}; Supplier {expense.supplier or ""}; Invoice {invoice.name if invoice else "unbooked expense"}'))
	for account, side in ((debit, 'debit'), (credit, 'credit')):
		currency = account.account_currency or base_currency
		account_rate = details['exchange_rate'] if currency == expense.currency else rate(currency, base_currency, payment_date)
		row = dict(account=account.name, account_currency=currency, exchange_rate=account_rate,
			cost_center=expense.cost_center, project=expense.project)
		row[side + '_in_account_currency'] = base_amount / account_rate
		if side == 'debit' and invoice:
			row.update(party_type='Supplier', party=invoice.supplier, reference_type='Purchase Invoice', reference_name=invoice.name)
		journal.append('accounts', row)
	previous_context = frappe.flags.get('import_expense_payment')
	frappe.flags.import_expense_payment = (expense.name, request_id)
	try:
		journal.insert()
		# ERPNext values invoice payable rows at the invoice's historical rate.
		# Recognize the difference against the bank's payment-date valuation.
		if journal.difference:
			field = 'exchange_gain_loss_account' if invoice else 'round_off_account'
			adjustment = frappe.get_cached_value('Company', expense.company, field)
			if not adjustment:
				frappe.throw(f'Set {field.replace("_", " ")} on Company to post the currency difference')
			adjustment_account = account_details(adjustment, expense.company)
			if adjustment_account.account_currency not in (None, '', base_currency):
				frappe.throw('Currency difference account must use company currency')
			journal.append('accounts', dict(account=adjustment, account_currency=base_currency,
				exchange_rate=1, cost_center=expense.cost_center or frappe.get_cached_value('Company', expense.company, 'cost_center'),
				project=expense.project, debit_in_account_currency=max(0, -journal.difference),
				credit_in_account_currency=max(0, journal.difference)))
			journal.save()
		journal.submit()
	finally:
		frappe.flags.import_expense_payment = previous_context
	return journal.name


def validate_payment_journal(doc, method=None):
	if doc.get('custom_import_expense') and frappe.flags.get('import_expense_payment') != (doc.custom_import_expense, doc.custom_payment_request):
		frappe.throw('Create expense payments using Create Payment on the Import Expense. Cancel and recreate a payment to change it.')


def update_payment_summary(doc, method=None):
	name = doc.get('custom_import_expense')
	if not name:
		return
	frappe.db.get_value('Import Expense', name, 'name', for_update=True)
	expense = frappe.get_doc('Import Expense', name)
	paid, outstanding = payment_totals(expense)
	frappe.db.set_value('Import Expense', name, dict(total_paid=paid, outstanding_amount=outstanding,
		payment_status='Paid' if outstanding == 0 else 'Partly Paid' if paid else 'Unpaid'), update_modified=False)


@frappe.whitelist()
def payment_history(expense_name):
	expense = frappe.get_doc('Import Expense', expense_name)
	expense.check_permission('read')
	if not frappe.has_permission('Journal Entry', 'read'):
		return []
	return frappe.get_list('Journal Entry', filters={'custom_import_expense': expense_name},
		fields=['name', 'posting_date', 'mode_of_payment', 'custom_payment_currency', 'custom_payment_exchange_rate', 'custom_payment_amount', 'docstatus'],
		order_by='posting_date desc, creation desc', limit_page_length=0)
