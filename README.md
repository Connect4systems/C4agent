# C4agent 1.0

C4agent is the import operations layer for ERPNext 15. It manages the complete purchase-to-import lifecycle while ERPNext remains the accounting, stock receipt, and valuation authority.

## Included phases

- Import Shipment, PO mapping, shipment items, manual container counts, documents, lifecycle workflow, closure and controlled reopening
- Foreign Purchase Invoice validation with ACID, shipping, PO and Sinosure references
- Purchase Receipt shipment validation and received-quantity summaries
- Import Shipment customs-clearance workflow; government costs are recorded as Import Expenses
- Import Expense Types, multi-currency expenses, recoverable VAT policy, approval workflow
- Standard ERPNext Landed Cost Voucher generation with exact expense traceability and duplicate-allocation protection
- Sinosure policy, per-shipment exposure, fees, expiry processing, approval workflow, and supplier exposure service
- Import Pipeline, Shipment Cost Summary, and Sinosure Exposure reports
- C4agent workspace, linked-document dashboard, six operational roles, audit comments, and configurable controls

The app never writes directly to GL Entry, Stock Ledger Entry, Bin, or item valuation. Purchase Invoices, Purchase Receipts, and Landed Cost Vouchers use standard ERPNext behavior.

## Supported platform

- Frappe 15
- ERPNext 15
- Python 3.10+

## Install or upgrade

From the bench directory:

```bash
bench --site green.connect4systems.com backup
bench --site green.connect4systems.com migrate
bench --site green.connect4systems.com clear-cache
bench build --app c4agent
sudo supervisorctl restart all
```

For a first installation, run `bench --site green.connect4systems.com install-app c4agent` before migrate.

## Configuration

Import Shipment requires a unique **Shipment ID** when creating a record, including drafts mapped from Purchase Orders. This ID becomes the document name and is available as a standard list filter. It can only be set on creation. Migration fills missing Shipment IDs on existing records with their current document names, preserving links.

Open **C4agent Settings** and review:

- goods-in-transit warehouse
- ACID requirement before departure
- customs release requirement before receipt
- landed cost requirement before closure
- partial shipment closure
- default import expense cost center and project

Assign users the base `Import User` role plus their operational role as appropriate. Finance and customs workflows use the dedicated manager roles.

## Test

```bash
bench --site green.connect4systems.com run-tests --app c4agent
```

Follow [TESTING_GUIDE.md](TESTING_GUIDE.md) for the complete business UAT.

## Key design rules

- A Purchase Order can be fulfilled by multiple Import Shipments.
- A shipment records No of Containers directly and can have multiple invoices, receipts, expenses, and LCVs.
- Import VAT is recoverable and excluded from landed cost by default.
- One Import Expense can belong to only one submitted LCV.
- Weight, volume, and manual allocations are entered through a standard manual ERPNext LCV and must reference the exact Import Expense row.
- Closing requires receipt, customs release, resolved expenses, logistics details, and landed cost unless an authorized documented override is used.

License: MIT

Import Container tracking has been replaced by editable **No of Containers** on Import Shipment. Run `bench --site your-site-name migrate` after deploying this update. The migration carries existing container counts forward and removes retired container metadata and integration fields. Package, gross weight, and CBM totals are now entered directly on the shipment.

## Import Expense payments

After approval, use **Actions > Create Payment**. The dialog defaults to today and the unpaid balance, fetches the expense currency and buying exchange rate, and defaults the bank/cash account from Mode of Payment for the company. Enter a smaller amount for a partial payment. Confirmation creates and submits a Journal Entry using the current user's accounting permissions.

Invoice-linked expenses settle the invoice payable account with Supplier and Purchase Invoice references. Unbooked expenses debit Expense / Tax Account. Expenses already linked to a Journal Entry or Payment Entry must be settled through that existing transaction to avoid duplicate expense recognition. Invoice payments are capped at both outstanding balances. Currency differences use the Company's Exchange Gain / Loss Account; non-invoice rounding differences use its Round Off Account.

Payment Status (Unpaid, Partly Paid, Paid), Total Paid, Outstanding Amount, and Journal Entry history track payments created through this action separately from approval and landed-cost allocation. Cancel a payment Journal Entry to reverse its payment totals; cancel existing payments before cancelling the expense. External payments reduce the invoice's available balance but are not automatically attributed to this expense's payment history.

Deploy with `bench --site green.connect4systems.com migrate` and restart the bench processes. Validate on a test site with same-currency and foreign-currency accounts before recording live payments. Local orchestration checks: `python -m unittest discover -s tests -p test_expense_payment_unit.py`.
