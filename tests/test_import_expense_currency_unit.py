"""Currency regression checks runnable without a Frappe site."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class ExpenseCurrencyTests(unittest.TestCase):
    def setUp(self):
        frappe = types.ModuleType("frappe")
        frappe.db = Mock()
        frappe.db.get_value.return_value = "EGP"
        frappe.throw = Mock(side_effect=ValueError("validation"))
        utils = types.ModuleType("frappe.utils")
        utils.flt = lambda value, precision=None: round(float(value or 0), precision) if precision is not None else float(value or 0)
        document = types.ModuleType("frappe.model.document")
        document.Document = type("Document", (), {})
        erp = types.ModuleType("erpnext.setup.utils")
        self.lookup = erp.get_exchange_rate = Mock(return_value=48)
        modules = {"frappe": frappe, "frappe.utils": utils,
                   "frappe.model": types.ModuleType("frappe.model"), "frappe.model.document": document,
                   "erpnext": types.ModuleType("erpnext"), "erpnext.setup": types.ModuleType("erpnext.setup"),
                   "erpnext.setup.utils": erp}
        path = Path(__file__).resolve().parents[1] / "c4agent/c4agent/doctype/import_expense/import_expense.py"
        spec = importlib.util.spec_from_file_location("isolated_import_expense", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(module)
        self.expense = module.ImportExpense()
        self.expense.__dict__.update(company="Company", currency="USD", posting_date="2026-08-01",
                                     exchange_rate=1, amount=100, docstatus=0,
                                     precision=lambda field: 2, get_doc_before_save=lambda: None)

    def test_posting_date_rate_replaces_default_or_invoice_rate(self):
        self.expense.set_currency_values()
        self.lookup.assert_called_once_with("USD", "EGP", "2026-08-01", "for_buying")
        self.assertEqual(self.expense.base_amount, 4800)
        self.expense.posting_date = "2026-08-02"
        self.lookup.return_value = 49
        self.expense.set_currency_values()
        self.lookup.assert_called_with("USD", "EGP", "2026-08-02", "for_buying")
        self.assertEqual(self.expense.base_amount, 4900)

    def test_company_currency_uses_one(self):
        self.expense.currency = "EGP"
        self.expense.set_currency_values()
        self.assertEqual(self.expense.exchange_rate, 1)
        self.lookup.assert_not_called()

    def test_missing_rate_cannot_keep_old_rate(self):
        self.lookup.return_value = None
        self.expense.set_currency_values()
        with self.assertRaises(ValueError):
            self.expense.validate_amount_and_exchange_rate()

    def test_missing_date_does_not_fall_back_to_today(self):
        self.expense.posting_date = None
        with self.assertRaises(ValueError):
            self.expense.set_currency_values()
        self.lookup.assert_not_called()

    def test_submission_fetches_rate(self):
        self.expense.docstatus = 1
        self.expense.get_doc_before_save = lambda: types.SimpleNamespace(docstatus=0)
        self.expense.set_currency_values()
        self.assertEqual(self.expense.exchange_rate, 48)

    def test_submitted_expense_preserves_rate(self):
        self.expense.docstatus = 1
        self.expense.get_doc_before_save = lambda: types.SimpleNamespace(docstatus=1)
        self.expense.exchange_rate = 45
        self.expense.set_currency_values()
        self.assertEqual(self.expense.base_amount, 4500)
        self.lookup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
