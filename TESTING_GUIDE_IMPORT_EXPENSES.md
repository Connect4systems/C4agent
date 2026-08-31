# Import Expense UAT Guide

This phase adds shipment/container cost attribution. It does not post accounting entries and does
not yet generate a Landed Cost Voucher.

## Deploy and migrate

```bash
cd ~/frappe-bench
bench --site green.connect4systems.com migrate
bench build --app c4agent
bench --site green.connect4systems.com clear-cache
bench --site green.connect4systems.com run-tests --app c4agent
```

Assign `Finance User` to users who prepare expenses. Finance approvers need both `Finance User`
and `Finance Manager` so they can edit active records and approve them.

## Verify setup

1. Open the C4agent workspace.
2. Confirm **Import Expense** appears under Finance.
3. Confirm **Import Expense Type** appears under Masters.
4. Review the seeded policies before entering live costs.
5. Set company-specific default accounts where appropriate. Seeded records intentionally do not
   create or guess Chart of Accounts entries.

## Test a shipment-level foreign-currency expense

1. Create Import Expense.
2. Select Company, Import Shipment, and `Ocean Freight`.
3. Leave Import Container blank.
4. Select the payee and a submitted Purchase Invoice if available.
5. Enter USD amount and the transaction exchange rate.
6. Select the company ledger account used by the linked accounting transaction.
7. Save.

Expected:

- Company-currency amount equals amount multiplied by exchange rate using ERPNext precision.
- Include in Landed Cost defaults to enabled.
- Allocation Basis defaults from Import Expense Type.
- No GL Entry or Stock Ledger Entry is created.

## Test a container-level expense

1. Create `Port Charges`, `Storage`, or `Demurrage` expense.
2. Select a container belonging to the shipment.
3. Try selecting a container belonging to another shipment.

Expected: the mismatched container is filtered in the UI and rejected by server validation.

## Test recoverable Import VAT

1. Create an expense with type `Import VAT`.
2. Save it.

Expected: Include in Landed Cost is disabled by default. Capitalizing it requires a Finance Manager
and a documented Landed Cost Override Reason.

## Test approval

1. Finance User selects **Submit for Verification**.
2. Finance Manager selects **Approve Expense**.

Expected: the document submits as Approved and shipment/container summaries refresh. Cancelling an
approved expense refreshes the summaries again.

## Current boundary

Do not mark expenses allocated manually. Exact expense-to-LCV mapping, allocation, cancellation
reversal, and shipment financial closure are delivered in the Landed Cost phase.
