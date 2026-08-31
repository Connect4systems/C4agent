# C4agent 1.0 deployment and UAT

Use a test company or test transactions. Do not submit accounting documents against live ledgers during UAT unless your finance team intends to keep them.

## 1. Deploy and verify setup

```bash
cd ~/frappe-bench
bench --site green.connect4systems.com backup
bench --site green.connect4systems.com migrate
bench --site green.connect4systems.com clear-cache
bench build --app c4agent
sudo supervisorctl restart all
bench --site green.connect4systems.com run-tests --app c4agent
```

Log out and in again. Confirm the C4agent workspace shows Operations, Finance, Masters, ERPNext Integration, and Reports. Confirm Import Expense is visible under Finance.

## 2. Master data and permissions

1. Assign `Import User` plus the appropriate manager, Customs, or Finance roles to test users.
2. Review C4agent Settings.
3. Mark the overseas supplier as **Is Foreign Supplier**.
4. Mark the customs broker and logistics suppliers with their respective flags.
5. Review the 18 seeded Import Expense Types and select valid company expense accounts.
6. Create a Shipping Line.

Expected: users see only actions allowed by their roles; no company account is hard-coded by the app.

## 3. Purchase and shipment

1. Create and submit a foreign-supplier Purchase Order.
2. Use **Create > Import Shipment** from the PO.
3. Enter shipped quantities, ACID and issue date, shipping details, ETD/ETA, and documents.
4. Create two shipments from the same PO if partial shipping is required.
5. Add one or more containers.
6. Progress Draft → Ordered → Booked → In Transit → Arrived.

Expected: the total shipped quantity across active shipments cannot exceed the PO; dates, container summaries, and watts are calculated; workflow prerequisites cannot be bypassed by direct saves.

## 4. Supplier invoice and Sinosure

1. Create Sinosure Coverage from the shipment.
2. Enter limit, previous exposure, shipment exposure, policy dates and optional fee data.
3. Progress Draft → Pending Approval → Approved → Active.
4. Create a Purchase Invoice for the foreign supplier and link the shipment.

Expected: remaining limit is calculated; negative remaining limit requires a Finance Manager reason; the invoice rejects a missing shipment, incomplete ACID/shipping data, wrong company/supplier, or unrelated PO.

## 5. Customs

1. Create a Customs Declaration from the shipment.
2. Enter the declaration number and government costs.
3. Confirm Total Customs Cost excludes recoverable Import VAT.
4. Add the submitted Purchase Invoice, Journal Entry, or Payment Entry used for accounting.
5. Progress through Documents Submitted, Review/Inspection, Duties Assessed, Payment Pending, Paid, and Released.

Expected: Paid/Released requires an accounting reference; Released requires a release date and updates the shipment clearance date. The shipment can then move to Cleared.

## 6. Receipt and import expenses

1. Create and submit one or more standard Purchase Receipts linked to the shipment.
2. Assign containers on receipt rows when the setting requires it.
3. Create Import Expenses for freight, duty, broker, port, transport, VAT and other customer-sheet costs.
4. Link each expense to the ERPNext accounting document that posted it.
5. Progress expenses through verification and approval.

Expected: currencies convert to company currency; the account must be a non-group company account; container-level totals update; Import VAT is excluded from landed cost by default; similar expenses warn but remain allowed.

## 7. Landed cost

1. From a Cleared or Received shipment choose **Create > Create Landed Cost Vouchers**.
2. Review the generated draft ERPNext LCVs and their exact Import Expense links.
3. Submit the LCVs.
4. Confirm only the referenced expenses become Allocated.
5. In a disposable test, cancel one LCV and confirm those expense flags reset.

Expected: Amount and Quantity bases are generated separately using standard ERPNext distribution. Weight, Volume, and Manual costs are added to a standard manual LCV and each charge row must select its exact Import Expense. Recoverable VAT is absent unless Finance Manager explicitly overrode it.

## 8. Closure, reports, and negative tests

1. Move the shipment to Received, then close it.
2. Confirm closure is blocked for missing receipt, customs release, required logistics data, pending expenses, unallocated costs, or partial receipt when disabled.
3. Test a documented manager override, then use **Reopen Shipment** with a mandatory reason.
4. Open all four reports and test their filters.
5. Try cancelling a shipment with submitted downstream documents.

Expected: closure/reopen and exceptions create timeline evidence; reopening changes operational status only and does not reverse accounting; reports reconcile to submitted expenses and ERPNext documents.

## Acceptance confirmation

Confirm these five totals against the customer workbook for the same shipment: supplier goods value, recoverable import VAT, total capitalizable import expenses, final LCV charges, and container totals. Record any rounding or policy difference before using the workflow on live imports.
