# C4agent Quick Start Guide

## 📋 What Was Just Built

**Milestone 1: Core Import Shipment & Container System** ✅ COMPLETE

### 5 New DocTypes
1. **Shipping Line** - Master record for shipping companies
2. **Import Shipment** - Central operational record tracking import shipments
3. **Import Shipment Item** - Line items within a shipment
4. **Import Container** - Individual container tracking
5. **C4agent Settings** - App configuration

### Custom Fields on 6 Existing DocTypes
- Supplier, Purchase Invoice, Purchase Receipt, Purchase Receipt Item, Landed Cost Voucher, Item

### 3 Integration Modules
- Purchase Invoice validation
- Purchase Receipt tracking
- Landed Cost Voucher allocation management

---

## 🚀 Installation Steps

```bash
# 1. Navigate to bench directory
cd /path/to/frappe-bench

# 2. Install the app
bench install-app c4agent

# 3. Run tests (optional but recommended)
bench --site {site_name} run-tests --app c4agent

# 4. Clear cache
bench --site {site_name} clear-cache
```

---

## ✨ First Time Setup

After installation:

1. **Go to C4agent Settings** (Desk > Search > C4agent Settings)
   - Configure default warehouse for goods-in-transit
   - Set validation requirements
   - Set cost center/project defaults

2. **Assign Users to Roles**
   - Go to Desk > User
   - Add roles: Import User, Import Manager, etc.

3. **Access C4agent Workspace**
   - Click workspace in sidebar
   - See all import-related documents in one place

---

## 📊 Basic Workflow

```
1. Create Purchase Order (ERPNext)
   ↓
2. Create Import Shipment (link to PO)
   ↓
3. Add Import Container (link to shipment)
   ↓
4. Update status (Draft → Ordered → Booked → ...)
   ↓
5. Track customs, expenses
   ↓
6. Receive in Purchase Receipt
   ↓
7. Generate Landed Cost Voucher
   ↓
8. Close Shipment
```

---

## 📁 Files Created Summary

```
Total: 24 files/folders created

DocTypes:       5 complete implementations
  ├── .json config files
  ├── .py Python classes
  └── __init__.py files

Integrations:   3 validation/event modules
  ├── purchase_invoice.py
  ├── purchase_receipt.py
  └── landed_cost_voucher.py

Setup:          1 module for custom fields & roles
  └── setup.py

Workspace:      1 UI configuration
  └── c4agent.json

Configuration:  1 updated hooks file
  └── hooks.py

Tests:          1 comprehensive test suite
  └── test_milestone_1.py

Documentation:  3 detailed guides
  ├── IMPLEMENTATION_BRIEF.md
  ├── MILESTONE_1_COMPLETE.md
  └── README.md (updated)
```

---

## 🔐 Roles Created

- **Import User**: View and manage shipments/containers
- **Import Manager**: Full operational control, status changes
- **Customs User**: Manage customs declarations  
- **Customs Manager**: Approve customs releases
- **Finance User**: Create import expenses
- **Finance Manager**: Approve expenses, override rules

---

## 🎯 Key Features

✅ **Shipment Lifecycle** - 9-step workflow from Draft to Closed  
✅ **Container Tracking** - Individual container management  
✅ **Validation** - Supplier/company matching, PO verification  
✅ **Auto-Calculations** - Totals, dates, currencies  
✅ **ERPNext Integration** - Links to PI, PR, LCV  
✅ **Workspace** - One-stop dashboard for operations  
✅ **Tests** - 10+ automated test cases included  

---

## 📝 Status Transitions

```
Draft ──→ Ordered ──→ Booked ──→ In Transit ──→ Arrived
   ↓         ↓          ↓           ↓             ↓
   └─→──────────────────┘     Under Customs  ──→ Cleared
                               Clearance ↑
                                 ↑_______│
                                          │
                                       Received ──→ Closed
```

Each transition has prerequisites that are validated server-side.

---

## 🧪 Testing

Run the included test suite:
```bash
bench --site {site_name} run-tests --app c4agent
```

Tests cover:
- Creating shipments from valid POs
- Supplier/company matching
- Container validation
- Date validations
- Status transitions

---

## 📖 Documentation Location

- **Architecture & Setup**: [README.md](README.md)
- **Full Specification**: [IMPLEMENTATION_BRIEF.md](IMPLEMENTATION_BRIEF.md)
- **Completion Report**: [MILESTONE_1_COMPLETE.md](MILESTONE_1_COMPLETE.md)
- **This Guide**: [QUICK_START.md](QUICK_START.md)

---

## ⚠️ Important Notes

1. **ERPNext Compatibility**: v15.0+
2. **Never Modify**: GL Entry, Stock Ledger, Bin, Item valuation_rate
3. **Permissions**: All validations are server-side (secure)
4. **Database**: No conflicts, migrations are clean and idempotent

---

## 🔜 What's Coming Next

**Milestone 2: Customs Workflow**
- Customs Declaration tracking
- ACID/Nafeza management
- Government fees and taxes

**Milestone 3: Import Expenses**
- Expense types and allocation
- Finance approval workflow
- Cost attribution by shipment/container

**Milestone 4: Landed Cost Integration**
- Auto-generate LCV from expenses
- Prevent duplicate allocation
- Stock valuation updates

**Milestone 5: Sinosure Coverage**
- Credit insurance tracking
- Exposure limits
- Policy monitoring

**Milestone 6: Reports**
- Import Pipeline report
- Cost summaries
- Exposure reports

---

## ❓ Common Tasks

### Create a New Shipment
1. Go to C4agent > Import Shipment > New
2. Select Company and Supplier
3. Link to existing Purchase Order
4. Fill in shipping details
5. Save (status = Draft)

### Add a Container
1. From Import Shipment, click "Import Container"
2. Enter container number and type
3. Fill dimensions and dates
4. Save

### Change Shipment Status
1. Open Import Shipment
2. Click status field
3. Select new status
4. Validations will check prerequisites
5. Save

### Generate Landed Cost
- Will be available in Milestone 4
- Auto-includes eligible import expenses
- Uses standard ERPNext LCV mechanism

---

**Version**: 0.1.0-alpha  
**Milestone**: 1 of 6  
**Status**: Ready for Testing

For questions or issues, refer to the full documentation files in the project root.
