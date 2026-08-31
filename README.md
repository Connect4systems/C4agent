## C4Agent - Import Management System for Frappe/ERPNext

Import and logistics management system for companies importing and distributing products (e.g., solar products). Tracks shipments, containers, customs declarations, import expenses, and integrates with ERPNext's standard accounting and stock management.

### Features

#### Core Import Management (Milestone 1 ✅ COMPLETED)
- **Import Shipment**: Central operational record linking PO to shipment lifecycle
- **Import Container**: Track individual containers with status, dates, and costs
- **Shipping Line Master**: Manage shipping companies and their information
- **Shipment Workflow**: Draft → Ordered → Booked → In Transit → Arrived → Customs → Cleared → Received → Closed
- **Custom Fields on Standard Doctypes**:
  - Supplier: foreign supplier, shipping agent, customs broker, logistics provider flags
  - Purchase Invoice: Import Shipment link with informational fields
  - Purchase Receipt: Import Shipment and Container links
  - Landed Cost Voucher: Import Shipment reference
  - Item: Wattage for solar panels

#### Planned Modules

**Milestone 2: Customs Workflow**
- Customs Declaration with ACID/Nafeza tracking
- Customs clearance workflow
- Government fees and taxes tracking

**Milestone 3: Expense Management**
- Import Expense types (freight, duties, broker fees, etc.)
- Shipment and container-level cost attribution
- Finance approval workflow

**Milestone 4: Landed Cost Integration**
- Automatic Landed Cost Voucher generation
- Prevention of duplicate cost allocation
- Proper stock valuation through ERPNext

**Milestone 5: Sinosure Coverage**
- Supplier credit insurance tracking
- Exposure limit management
- Policy and coverage monitoring

**Milestone 6: Reports & Dashboard**
- Import Pipeline report
- Shipment Cost Summary
- Container Cost Summary
- Sinosure Exposure report

### Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/connect4systems/c4agent.git --branch main
bench install-app c4agent
```

### Requirements

- Frappe Framework v15.0 or higher
- ERPNext v15.0 or higher

### Architecture

The app follows a clean separation of concerns:

```
Import Shipment (Operational Truth)
    ↓
    +-- Import Container (Container tracking)
    +-- Purchase Invoice (Accounting link)
    +-- Purchase Receipt (Stock receipt)
    +-- Customs Declaration (Regulatory)
    +-- Import Expense (Cost attribution)
    +-- Sinosure Coverage (Credit exposure)
    ↓
Landed Cost Voucher (Stock valuation)
    ↓
ERPNext GL & Stock Ledger (Posted Truth)
```

**Key Principle**: C4agent is an operational/logistics layer that organizes import processes. It never directly modifies ERPNext's accounting or stock ledgers. All GL and stock changes happen through standard ERPNext documents (Purchase Invoice, Purchase Receipt, Landed Cost Voucher).

### Roles

- **Import User**: Create/view shipments and containers
- **Import Manager**: Operational control and status transitions
- **Customs User**: Manage customs declarations
- **Customs Manager**: Approve customs clearance
- **Finance User**: Create import expenses
- **Finance Manager**: Approve expenses, override rules, manage closure

### Key Business Rules

1. One PO can create multiple Import Shipments (not 1:1)
2. One Shipment can have multiple Containers, Purchase Receipts, and Purchase Invoices
3. Container must belong to the selected shipment
4. Recoverable Import VAT is excluded from landed cost by default
5. No duplicate landed-cost allocation allowed
6. Shipment closure blocked without resolved landed-cost expenses
7. Never directly modify GL Entry or Stock Ledger

### Setup

1. **Create Roles** (automatic on install)
2. **Add Users to Roles** (via Security > User)
3. **Configure C4agent Settings** (C4Agent > Settings)
   - Default warehouse for goods-in-transit
   - Validation requirements (ACID, containers, customs release, etc.)
   - Cost center and project defaults

### Usage Workflow

#### Standard Import Flow

1. **Create Purchase Order** in ERPNext
   - Supplier, company, items, quantities

2. **Create Import Shipment**
   - Link to PO
   - Set supplier currency
   - Add shipping details (line, port, dates, ACID, etc.)
   - Add items (auto-fetched from PO)

3. **Add Containers**
   - Container number, type, dimensions
   - Track movement through customs

4. **Create Customs Declaration**
   - Link ACID, Nafeza, CargoX references
   - Track duties and fees
   - Record clearance status

5. **Record Import Expenses**
   - Ocean freight, customs broker, port charges, etc.
   - Assign to shipment or specific containers
   - Link to actual Purchase Invoices/Journal Entries

6. **Create Purchase Receipt** (in ERPNext)
   - Receive goods into warehouse
   - Link to Import Shipment and Container
   - Standard ERPNext stock receipt

7. **Generate Landed Cost Voucher** (in ERPNext)
   - Auto-generate from Import Shipment
   - Automatically includes eligible import expenses
   - ERPNext updates stock valuation

8. **Close Import Shipment**
   - Validates all prerequisites
   - Records closure timestamp and user
   - Marks shipment complete

### Workspace

Access the C4agent workspace from the desk to see:

**Operations**
- Import Shipment
- Import Container  
- Customs Declaration

**Finance**
- Import Expense
- Sinosure Coverage

**Masters**
- Shipping Line
- Import Expense Type
- C4agent Settings

**ERPNext Integration**
- Purchase Order
- Purchase Invoice
- Purchase Receipt
- Landed Cost Voucher

**Reports**
- Import Pipeline

### Development

#### Code Structure

```
c4agent/
├── c4agent/
│   ├── doctype/
│   │   ├── import_shipment/
│   │   ├── import_shipment_item/
│   │   ├── import_container/
│   │   ├── shipping_line/
│   │   ├── c4agent_settings/
│   │   ├── customs_declaration/         (Milestone 2)
│   │   ├── import_expense/               (Milestone 3)
│   │   ├── import_expense_type/          (Milestone 3)
│   │   └── sinosure_coverage/            (Milestone 5)
│   ├── integrations/
│   │   ├── purchase_invoice.py
│   │   ├── purchase_receipt.py
│   │   └── landed_cost_voucher.py
│   ├── services/
│   │   ├── shipment.py
│   │   ├── costing.py
│   │   └── sinosure.py
│   └── tests/
│       └── test_milestone_1.py
├── hooks.py
└── setup.py
```

#### Testing

```bash
bench --site {site_name} run-tests --app c4agent
```

#### Code Style

This app uses pre-commit hooks for code quality:

```bash
cd apps/c4agent
pre-commit install
```

Tools: ruff (linting/formatting), eslint, prettier, pyupgrade

### Contributing

1. Create a feature branch
2. Implement feature with tests
3. Ensure pre-commit passes
4. Submit pull request to `develop` branch

### Support for Custom Fields

If modifying existing doctypes, ensure migrations are:
1. Idempotent (safe to run multiple times)
2. Don't create duplicate custom fields
3. Use `ignore_if_duplicate=True` where appropriate

### Known Limitations (Version 1.0)

- No partial landed-cost allocation (single LCV per expense)
- Container-level cost aggregation simplified (full implementation in future)
- Sinosure is credit-tracking, not banking integration
- No multi-currency ledger (uses ERPNext base currency for reporting)

### Future Enhancements

- Partial shipment closure
- Partial landed-cost allocation
- Container tracking API integration
- Customs brokerage API integration
- Advanced cost allocation by weight/quantity/manual
- Cost-per-watt reporting for solar panels

### License

MIT

### Support

For issues, questions, or contributions:
- Create an issue in the repository
- Contact: info@connect4systems.com

---

**Last Updated**: 2026-08-31
**Version**: 0.1.0 (Milestone 1 Beta)

