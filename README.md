# C4agent 1.0

C4agent is the import operations layer for ERPNext 15. It manages the complete purchase-to-import lifecycle while ERPNext remains the accounting, stock receipt, and valuation authority.

## Included phases

- Import Shipment, PO mapping, shipment items, containers, documents, lifecycle workflow, closure and controlled reopening
- Foreign Purchase Invoice validation with ACID, shipping, PO and Sinosure references
- Purchase Receipt shipment/container validation and received-quantity summaries
- Customs Declaration, government costs, accounting references, and clearance workflow
- Import Expense Types, multi-currency expenses, recoverable VAT policy, approval workflow, and container cost summaries
- Standard ERPNext Landed Cost Voucher generation with exact expense traceability and duplicate-allocation protection
- Sinosure policy, per-shipment exposure, fees, expiry processing, approval workflow, and supplier exposure service
- Import Pipeline, Shipment Cost Summary, Container Cost Summary, and Sinosure Exposure reports
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

Open **C4agent Settings** and review:

- goods-in-transit warehouse
- ACID requirement before departure
- customs release requirement before receipt
- container requirements
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
- A shipment can have multiple containers, invoices, receipts, expenses, and LCVs.
- Import VAT is recoverable and excluded from landed cost by default.
- One Import Expense can belong to only one submitted LCV.
- Weight, volume, and manual allocations are entered through a standard manual ERPNext LCV and must reference the exact Import Expense row.
- Closing requires receipt, customs release, resolved expenses, logistics details, and landed cost unless an authorized documented override is used.

License: MIT
