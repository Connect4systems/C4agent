import frappe


def execute():
	frappe.db.sql('''update `tabImport Expense`
		set total_paid=0, outstanding_amount=amount, payment_status='Unpaid'
		where coalesce(total_paid, 0)=0''')
