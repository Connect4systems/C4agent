C4AGENT - FRAPPE / ERPNEXT IMPORT MANAGEMENT APP
IMPLEMENTATION BRIEF FOR CODEX / AI DEVELOPMENT AGENT
======================================================

PROJECT
-------

Build a custom Frappe/ERPNext app for an Egyptian company that imports and distributes solar products.

App technical name:
c4agent

App title:
C4agent

Target:
Frappe / ERPNext v15+

IMPORTANT:
- Do not modify ERPNext core files.
- Inspect the actual installed Frappe/ERPNext version before implementing integrations.
- Use standard ERPNext accounting, stock, Purchase Receipt, Purchase Invoice, and Landed Cost Voucher behavior wherever possible.
- The custom app is the import/logistics management layer, not a replacement accounting or stock engine.
- Business-critical validation must be server-side.
- Do not directly write to GL Entry, Stock Ledger Entry, Bin, valuation_rate, or other accounting/stock internals.

======================================================================
1. BUSINESS OBJECTIVE
======================================================================

The company imports and distributes products such as:

- Solar Panels
- Inverters
- Batteries
- Cables
- Structures
- Solar Pumps
- Accessories

Each import can involve:

- Purchase Order
- Supplier Invoice
- ACID / Nafeza
- CargoX documents
- Shipping Line
- Bill of Lading
- Vessel
- Voyage
- One or more Containers
- Customs Declaration
- Customs Duties
- Import VAT
- Import Tax
- Nafeza Fees
- Inspection / Quarantine
- Port Expenses
- Ocean Freight
- Customs Broker
- Transportation
- Storage
- Demurrage / Detention
- Marine Insurance
- Bank Charges
- Sinosure Coverage
- Purchase Receipt
- Landed Cost Voucher

The central operational record must be:

Import Shipment

Relationship:

Purchase Order
    |
    v
Import Shipment
    |
    +-- Import Containers
    +-- Purchase Invoices
    +-- Customs Declarations
    +-- Import Expenses
    +-- Sinosure Coverage
    +-- Purchase Receipts
    +-- Landed Cost Vouchers

Import Shipment is the operational master record.

ERPNext standard accounting documents remain the accounting truth.
ERPNext Purchase Receipt remains the stock receipt truth.
ERPNext Landed Cost Voucher remains the inventory valuation mechanism.

## KEY BUSINESS RULES

RULE 1: Import Shipment is logistics/operational truth.
RULE 2: ERPNext accounting documents are accounting truth.
RULE 3: Purchase Receipt is stock receipt truth.
RULE 4: Landed Cost Voucher is inventory valuation mechanism.
RULE 5: Import Expense attributes costs but must never duplicate accounting entries.
RULE 6: Recoverable Import VAT is not automatically capitalized.
RULE 7: One Import Shipment can have many Containers.
RULE 8: One Import Shipment can have many Purchase Receipts.
RULE 9: One Import Shipment can have many Purchase Invoices.
RULE 10: One Purchase Order may create multiple Import Shipments.
RULE 11: Container-level costs must be traceable.
RULE 12: Shipment cannot close with unresolved eligible landed-cost expenses.
RULE 13: Sinosure is credit insurance / exposure management, not banking.
RULE 14: Never modify ERPNext core.
RULE 15: Never post directly to GL Entry or Stock Ledger Entry.

## IMPLEMENTATION MILESTONES

### MILESTONE 1: Core Shipment and Container Lifecycle
- Initialize C4agent app
- Workspace
- Import Shipment DocType
- Import Shipment Item (child table)
- Import Container DocType
- Shipping Line master
- Shipment workflow
- Purchase Order integration
- Purchase Invoice link
- Purchase Receipt link
- Container on Purchase Receipt Item

### MILESTONE 2: Customs Workflow
- Customs Declaration
- ACID / Nafeza fields
- Customs workflow
- Import Shipment Documents
- Customs accounting references

### MILESTONE 3: Expense Management
- Import Expense DocType
- Import Expense Type master
- Finance approval workflow
- Shipment/container cost attribution
- Cost summary fields

### MILESTONE 4: Landed Cost Integration
- Landed Cost Voucher integration
- LCV generation method
- Duplicate allocation prevention
- LCV cancellation handling
- Shipment closure validation

### MILESTONE 5: Sinosure Coverage
- Sinosure Coverage DocType
- Exposure tracking
- Limits and expiry management
- Workflow and alerts

### MILESTONE 6: Reports & Dashboard
- Import Pipeline report
- Shipment Cost Summary
- Container Cost Summary
- Sinosure Exposure report
- Workspace cards/dashboard

## CODE ARCHITECTURE

```
c4agent/
├── c4agent/
│   ├── hooks.py
│   ├── modules.txt
│   ├── c4agent/
│   │   ├── doctype/
│   │   │   ├── import_shipment/
│   │   │   ├── import_shipment_item/
│   │   │   ├── import_container/
│   │   │   ├── customs_declaration/
│   │   │   ├── import_expense/
│   │   │   ├── import_expense_type/
│   │   │   ├── shipping_line/
│   │   │   ├── sinosure_coverage/
│   │   │   ├── import_shipment_document/
│   │   │   └── c4agent_settings/
│   │   ├── report/
│   │   │   ├── import_pipeline/
│   │   │   ├── shipment_cost_summary/
│   │   │   ├── container_cost_summary/
│   │   │   └── sinosure_exposure/
│   │   └── workspace/
│   ├── integrations/
│   │   ├── purchase_invoice.py
│   │   ├── purchase_receipt.py
│   │   └── landed_cost_voucher.py
│   ├── services/
│   │   ├── shipment.py
│   │   ├── costing.py
│   │   ├── sinosure.py
│   │   └── status.py
│   └── fixtures/
└── README.md
```

## NEXT STEPS

1. Verify installed Frappe/ERPNext version
2. Review current c4agent structure
3. Implement MILESTONE 1: Core Shipment and Container Lifecycle
