"""Unit checks for payment orchestration; runnable without a Frappe site."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.frappe = types.ModuleType('frappe')
        self.frappe.whitelist = lambda: lambda fn: fn
        self.frappe.throw = Mock(side_effect=ValueError('validation'))
        self.frappe.PermissionError = PermissionError
        self.frappe.flags = Mock()
        self.frappe.flags.get.return_value = None
        self.frappe.db = Mock()
        self.frappe.db.get_value.return_value = None
        self.frappe.has_permission = Mock(return_value=True)
        self.frappe.get_cached_value = Mock(return_value='EGP')
        self.frappe.get_all = Mock(return_value=[])
        utils = types.ModuleType('frappe.utils')
        utils.flt = lambda n, precision=None: round(float(n or 0), precision) if precision is not None else float(n or 0)
        utils.getdate = lambda n: n
        utils.nowdate = lambda: '2026-09-11'
        erp = types.ModuleType('erpnext.setup.utils')
        erp.get_exchange_rate = Mock(return_value=50)
        modules = {'frappe': self.frappe, 'frappe.utils': utils, 'erpnext': types.ModuleType('erpnext'), 'erpnext.setup': types.ModuleType('erpnext.setup'), 'erpnext.setup.utils': erp}
        path = Path(__file__).resolve().parents[1] / 'c4agent/c4agent/services/expense_payment.py'
        spec = importlib.util.spec_from_file_location('isolated_payment_service', path)
        self.service = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(self.service)
        self.expense = types.SimpleNamespace(name='EXP-1', amount=100, currency='USD', company='Company', import_shipment='SHIP-1', supplier='Supplier', supplier_invoice=None, accounting_reference_name=None, expense_account='Expense', cost_center='Main', project=None, precision=lambda field: 2, docstatus=1, expense_status='Approved', check_permission=Mock())
        self.frappe.get_doc = Mock(return_value=self.expense)
        self.journal = Mock(name='journal')
        self.journal.name = 'JV-1'
        self.journal.difference = 0
        self.journal.flags = types.SimpleNamespace()
        self.frappe.new_doc = Mock(return_value=self.journal)

    def setup_create(self, invoice=None, maximum=100):
        self.service.invoice_for = Mock(return_value=invoice)
        self.service.payment_details = Mock(return_value={'amount': maximum, 'exchange_rate': 50})
        def account(name, company):
            return types.SimpleNamespace(name=name, account_type='Bank' if name=='Bank' else 'Payable' if name=='Payable' else 'Expense Account', account_currency='EGP')
        self.service.account_details = Mock(side_effect=account)

    def create(self, amount=40):
        return self.service.create_payment('EXP-1', '2026-09-11', 'Transfer', 'Bank', amount, 'request-1')

    def test_partial_unbooked_posts_balanced_debit_and_credit(self):
        self.setup_create()
        self.assertEqual(self.create(), 'JV-1')
        rows = [c.args[1] for c in self.journal.append.call_args_list]
        self.assertEqual(rows[0]['account'], 'Expense')
        self.assertEqual(rows[0]['debit_in_account_currency'], 2000)
        self.assertEqual(rows[1]['credit_in_account_currency'], 2000)
        self.journal.submit.assert_called_once()

    def test_invoice_payment_references_supplier_and_invoice(self):
        invoice = types.SimpleNamespace(name='PI-1', credit_to='Payable', supplier='Supplier', reload=Mock())
        self.setup_create(invoice)
        self.create()
        row = self.journal.append.call_args_list[0].args[1]
        self.assertEqual((row['account'], row['party_type'], row['party'], row['reference_type'], row['reference_name']), ('Payable','Supplier','Supplier','Purchase Invoice','PI-1'))

    def test_overpayment_zero_negative_rejected(self):
        self.setup_create(maximum=30)
        for amount in (40, 0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError): self.create(amount)
        self.journal.insert.assert_not_called()

    def test_retry_returns_existing_journal_without_posting(self):
        self.frappe.db.get_value.return_value = types.SimpleNamespace(name='JV-OLD', docstatus=1)
        self.assertEqual(self.create(), 'JV-OLD')
        self.frappe.new_doc.assert_not_called()

    def test_permissions_enforced(self):
        self.frappe.has_permission.return_value = False
        with self.assertRaises(ValueError): self.create()
        self.frappe.new_doc.assert_not_called()

    def test_unapproved_rejected(self):
        self.expense.docstatus=0
        with self.assertRaises(ValueError): self.service.approved_expense('EXP-1')

    def test_already_booked_journal_reference_rejected(self):
        self.expense.accounting_reference_name='JV-BOOKED'
        self.expense.accounting_reference_doctype='Journal Entry'
        with self.assertRaises(ValueError): self.service.invoice_for(self.expense)

    def test_status_recalculates_after_full_partial_and_cancelled_payments(self):
        doc=Mock();doc.get.return_value='EXP-1'
        for amounts, status, outstanding in (([40], 'Partly Paid', 60), ([40,60], 'Paid', 0), ([], 'Unpaid',100)):
            self.frappe.get_all.return_value=[types.SimpleNamespace(custom_payment_amount=n) for n in amounts]
            self.service.update_payment_summary(doc)
            values=self.frappe.db.set_value.call_args.args[2]
            self.assertEqual(values['payment_status'],status)
            self.assertEqual(values['expense_status'], status if status != 'Unpaid' else 'Approved')
            self.assertEqual(values['outstanding_amount'],outstanding)

    def test_invoice_balance_caps_default_payment_in_expense_currency(self):
        invoice=types.SimpleNamespace(credit_to='Payable',outstanding_amount=1500)
        self.service.invoice_for=Mock(return_value=invoice)
        self.service.account_details=Mock(return_value=types.SimpleNamespace(account_currency='EGP'))
        result=self.service.payment_details('EXP-1')
        self.assertEqual(result['amount'],30)

    def test_currency_gain_loss_balances_historical_invoice_rate(self):
        self.setup_create(types.SimpleNamespace(name='PI-1',credit_to='Payable',supplier='Supplier',reload=Mock()))
        self.journal.difference=-100
        self.create()
        adjustment=self.journal.append.call_args_list[-1].args[1]
        self.assertEqual(adjustment['debit_in_account_currency'],100)
        self.journal.save.assert_called_once()

    def test_same_currency_rate_and_missing_foreign_rate(self):
        self.assertEqual(self.service.rate('EGP','EGP','2026-09-11'),1)
        self.service.get_exchange_rate.return_value=0
        with self.assertRaises(ValueError): self.service.rate('USD','EGP','2026-09-11')


if __name__=='__main__': unittest.main()
