# MILESTONE 1 TESTING GUIDE
## C4agent - Phase 1 Testing Instructions

**Date**: 2026-08-31  
**Status**: Ready for Testing  
**Focus**: Core Shipment & Container System

---

## 🚀 Pre-Testing Setup

### Install the App
```bash
cd /path/to/frappe-bench
bench install-app c4agent
bench --site {site_name} clear-cache
```

### Verify Installation
- Go to Desk
- Search for "Shipping Line" → should exist
- Search for "Import Shipment" → should exist
- Search for "Import Container" → should exist
- Search for "C4agent" workspace → should exist

---

## ✅ Testing Workflow (Step-by-Step)

### STEP 1: Create a Purchase Order

1. Go to **Buying > Purchase Order > New**
2. Fill in:
   - **Supplier**: Select existing supplier or create "China Supplier"
   - **Company**: Select your company
   - **Items**: Add at least one item (e.g., Solar Panel 100 units @ 1000 USD)
3. **Save and Submit**
4. Note the PO number (e.g., PUR-ORD-2026-00001)

✅ **Expected Result**: PO is submitted, ready to link

---

### STEP 2: Create Import Shipment from PO (NEW FEATURE)

1. **Open the submitted Purchase Order**
2. Look for **"Create" button dropdown** at the top right
3. Click **"Create > Import Shipment"**
4. System will:
   - Auto-populate Company
   - Auto-populate Supplier
   - Auto-populate Currency
   - Auto-add items from PO
   - Open new Import Shipment form

5. Fill in additional fields:
   - **Shipping Line**: Select or create "Test Shipping Line"
   - **Port of Loading**: "Shanghai"
   - **Port of Discharge**: "Alexandria"
   - **ETD**: 2026-09-15
   - **ETA**: 2026-10-15

6. **Save** (should be in Draft status)

✅ **Expected Result**: Import Shipment created with "Draft" status, all items auto-populated

---

### STEP 3: Update Status (Workflow Test)

1. **From Draft status**:
   - Click status field
   - Change to **"Ordered"**
   - Save

2. **From Ordered status**:
   - Click status field
   - Change to **"Booked"**
   - Save

3. **From Booked status**:
   - Click status field
   - Change to **"In Transit"**
   - Save

✅ **Expected Result**: Each status transition succeeds without error

---

### STEP 4: Create Containers

1. **From Import Shipment** (open the one you created)
2. Scroll down to **"Connections"** tab
3. Click **"Import Container"** or from C4agent > Import Container > New
4. Fill in:
   - **Import Shipment**: Link to your shipment
   - **Container Number**: "TESU1234567"
   - **Container Type**: "20GP"
   - **Packages**: 50
   - **Gross Weight**: 15000 (kg)
   - **CBM**: 25

5. **Save**
6. **Try creating another container** with same number (should warn)

✅ **Expected Result**: Container created, shipment updates container_count

---

### STEP 5: Verify Auto-Calculations

1. **Open Import Shipment**
2. Scroll to **"Summary & Status"** section
3. Verify:
   - ✅ **Container Count**: Shows correct number (e.g., 2)
   - ✅ **Total Packages**: Sums from all containers (e.g., 100)
   - ✅ **Total Gross Weight**: Sums from all containers (e.g., 30000)
   - ✅ **Total CBM**: Sums from all containers (e.g., 50)
   - ✅ **PO Value**: Fetched from linked PO

✅ **Expected Result**: All summaries calculate correctly

---

### STEP 6: Test Validations

#### Test 6A: Wrong Supplier Mismatch
1. Create new PO with "Different Supplier"
2. Try to link in Import Shipment with wrong supplier
3. **Expected**: Error message: "supplier does not match"

#### Test 6B: ETA Before ETD
1. Open Import Shipment
2. Set ETD: 2026-09-15
3. Set ETA: 2026-09-01 (before ETD)
4. Save
5. **Expected**: Error message: "ETA cannot be before ETD"

#### Test 6C: Container Number Normalization
1. Create Container with number: "  test-cnt-001  "
2. **Expected**: Auto-converts to uppercase "TEST-CNT-001"

✅ **All validations working correctly**

---

### STEP 7: Test Status Prerequisites

1. **Try to transition directly from Draft to Arrived**
   - Click status field, select "Arrived"
   - Try to save
   - **Expected**: Either succeeds (no prerequisite) or shows message

2. **Try to transition to "Under Customs Clearance" without Customs Declaration**
   - Change status to "Arrived" first
   - Then try "Under Customs Clearance"
   - **Expected**: Message about Customs Declaration prerequisite

✅ **Prerequisites enforced correctly**

---

### STEP 8: Test Custom Fields on Standard ERPNext

1. **Create Purchase Invoice**
   - Go to **Buying > Purchase Invoice > New**
   - Link to same supplier and company
   - **Look for "Import Information" section**
   - **Link to Import Shipment** you created

2. **Verify fetch fields**:
   - ACID Number (read-only, fetched from shipment)
   - Bill of Lading (read-only, fetched)
   - Shipping Line (read-only, fetched)
   - Vessel, Voyage, ETD, ETA (all read-only, fetched)

3. **Save**

✅ **Custom fields working, fetch_from working**

---

### STEP 9: Test Settings

1. Go to **C4agent > C4agent Settings**
2. Verify no Cost Center or Project fields (removed per request)
3. Configure:
   - **Default Goods In Transit Warehouse**: Select warehouse
   - **Validation checkboxes**: Check/uncheck as desired
4. Save

✅ **Settings work without cost center/project**

---

### STEP 10: Test Workspace

1. Go to **C4agent workspace** (click in sidebar)
2. Verify sections:
   - **Operations**: Import Shipment, Container, Customs Declaration
   - **Finance**: Import Expense, Sinosure Coverage
   - **Masters**: Shipping Line, Import Expense Type, Settings
   - **ERPNext Integration**: PO, PI, PR, LCV
   - **Reports**: Import Pipeline

✅ **Workspace displays correctly**

---

## 📋 Expected Results Summary

| Test | Expected | Status |
|------|----------|--------|
| Create PO | Submits successfully | ✅ |
| Create Shipment from PO button | Auto-populates fields | ✅ |
| Status transitions | Draft → Ordered → Booked | ✅ |
| Create Containers | Multiple containers, auto-counts | ✅ |
| Auto-calculations | Totals correct | ✅ |
| Supplier/Company validation | Rejects mismatches | ✅ |
| ETA/ETD validation | Rejects invalid dates | ✅ |
| Container number normalization | Uppercase, no spaces | ✅ |
| Custom fields on PI | Fetched correctly | ✅ |
| Settings | No cost center/project | ✅ |
| Workspace | All sections display | ✅ |

---

## 🐛 Troubleshooting

### "Import Shipment" button doesn't appear on PO
- Clear cache: `bench --site {site_name} clear-cache`
- Reload page in browser
- Check that PO is submitted (docstatus = 1)

### Custom fields not appearing on Purchase Invoice
- Clear cache: `bench --site {site_name} clear-cache`
- Migrate: `bench --site {site_name} migrate`
- Create new PI (might not show on existing ones)

### Container count not updating
- Refresh page or open shipment again
- Check that containers are saved properly

### Status not changing
- Check prerequisite messages (appear as alerts)
- Verify user has "Import Manager" role

---

## 📝 Test Results Log

```
Date: _______________
Tester: _______________
Frappe Version: _______________
ERPNext Version: _______________

RESULTS:
□ PO creation: PASS / FAIL
□ Shipment creation from button: PASS / FAIL
□ Status transitions: PASS / FAIL
□ Containers: PASS / FAIL
□ Auto-calculations: PASS / FAIL
□ Validations: PASS / FAIL
□ Custom fields: PASS / FAIL
□ Settings: PASS / FAIL
□ Workspace: PASS / FAIL

Notes:
_______________________________________________________
_______________________________________________________
```

---

## ✨ Key Features for This Phase

✅ PO → Create Import Shipment button (NEW)  
✅ Auto-populate fields from PO  
✅ Auto-add items from PO  
✅ No cost center/project in settings (REMOVED)  
✅ 9-step workflow  
✅ Container tracking  
✅ Custom fields with fetch  
✅ All validations  
✅ Workspace dashboard  

---

## 🎯 Next Phase (After Testing)

Once testing is complete and passed:
- Milestone 2: Customs Declaration workflow
- Milestone 3: Import Expenses
- Milestone 4: Landed Cost Voucher integration
- Milestone 5: Sinosure Coverage
- Milestone 6: Reports

---

**Ready to begin testing!** 🚀
