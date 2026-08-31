# INSTALLATION VERIFICATION CHECKLIST

## After Running: `bench install-app c4agent`

### 1. Database Verification ✓

Check that all DocTypes are created:

```bash
# Run this in bench console or via Frappe API
bench --site {site_name} eval "from frappe import db; docetypes = ['Import Shipment', 'Import Container', 'Shipping Line', 'Import Shipment Item', 'C4agent Settings']; print([dt for dt in doctypes if db.exists('DocType', dt)])"
```

Expected output: All 5 DocTypes should exist

### 2. Custom Fields Verification ✓

Verify custom fields were added to standard doctypes:

1. Go to **Setup > Customize Form > Purchase Invoice**
   - Should see: `custom_import_shipment` field
   - Should see: "Import Information" section

2. Go to **Setup > Customize Form > Purchase Receipt**
   - Should see: `custom_import_shipment` field

3. Go to **Setup > Customize Form > Item**
   - Should see: `custom_wattage` field

### 3. Roles Verification ✓

Check roles were created:

1. Go to **Setup > Role**
2. Search for each role (should all exist):
   - [ ] Import User
   - [ ] Import Manager
   - [ ] Customs User
   - [ ] Customs Manager
   - [ ] Finance User
   - [ ] Finance Manager

### 4. Workspace Verification ✓

1. Look for **C4agent** workspace in sidebar
2. Should contain sections:
   - [ ] Operations (Shipment, Container, Customs)
   - [ ] Finance (Expense, Sinosure)
   - [ ] Masters (Shipping Line, Expense Type, Settings)
   - [ ] ERPNext Integration (PO, PI, PR, LCV)
   - [ ] Reports

### 5. Custom Button Verification ✓

**THIS IS THE KEY TEST**

1. Go to **Buying > Purchase Order**
2. Create and submit a new PO:
   ```
   Supplier: Any supplier
   Company: Your company
   Item: Add any item with qty
   ```
3. After submitting, click **"Create"** button dropdown
4. Look for **"Import Shipment"** option
   
   ✅ **If you see it**: Button is working!
   ❌ **If you don't see it**: Run these commands:
   ```bash
   bench --site {site_name} clear-cache
   bench build
   bench restart
   ```

### 6. Settings Verification ✓

1. Go to **C4Agent > C4agent Settings**
2. Verify these fields exist:
   - [ ] Default Goods In Transit Warehouse
   - [ ] Require ACID Before Departure
   - [ ] Require Container Number
   - [ ] Require Customs Release Before Receipt
   - [ ] Require Landed Cost Before Closing
   - [ ] Allow Partial Shipment Closure
   - [ ] Require Container on Purchase Receipt Item

3. ✅ **Verify these DON'T exist** (removed for testing):
   - ❌ default_import_expense_cost_center
   - ❌ default_import_expense_project

### 7. Create First Shipment Test ✓

1. **Create Purchase Order**:
   - Supplier: "China Supplier"
   - Company: Your company
   - Add item: Solar Panel, Qty: 100, Rate: 1000
   - **Submit**

2. **Create Import Shipment from Button**:
   - Click "Create > Import Shipment"
   - New form should open with auto-populated fields:
     - Company: ✅ Same as PO
     - Supplier: ✅ Same as PO
     - Currency: ✅ Fetched from PO
     - Items: ✅ Added from PO
   - Save

3. **Verify Auto-Calculations**:
   - Shipment title should be auto-generated
   - PO value should show in summary

### 8. Status Workflow Test ✓

1. From Draft Import Shipment:
   - [ ] Can change to "Ordered"
   - [ ] Can change to "Booked"
   - [ ] Can change to "In Transit"
   - [ ] Can change to "Arrived"

### 9. Container Test ✓

1. From Import Shipment, create Import Container:
   - Container Number: "TESU1234567"
   - Container Type: "20GP"
   - Save

2. Verify:
   - [ ] Container number normalized to uppercase
   - [ ] Shipment's container_count updated
   - [ ] Can create multiple containers

### 10. Custom Fields Test ✓

1. **Create Purchase Invoice**:
   - Link to same supplier & company as shipment
   - Go to "Import Information" section
   - [ ] Can link to Import Shipment
   - [ ] ACID Number fetches automatically
   - [ ] Bill of Lading fetches automatically
   - [ ] Shipping Line fetches automatically

---

## Summary Table

| Component | Status | Notes |
|-----------|--------|-------|
| DocTypes (5) | ✓ | All should exist in DB |
| Custom Fields (16) | ✓ | Added to 6 standard doctypes |
| Roles (6) | ✓ | All created, need user assignment |
| Workspace | ✓ | C4agent should be in sidebar |
| PO Button | ✓ | Most important - test carefully |
| Settings | ✓ | No cost center/project fields |
| First Shipment | ✓ | Create from PO button |
| Auto-calculations | ✓ | Totals, title, currency |
| Validations | ✓ | Error messages on constraints |
| Custom fields on PI | ✓ | Fetch_from working |

---

## If Something Fails

### Clear Cache (Most Common Fix)
```bash
bench --site {site_name} clear-cache
bench build
bench restart
```

### Reinstall App
```bash
bench uninstall-app c4agent
bench get-app https://github.com/connect4systems/c4agent.git
bench install-app c4agent
bench --site {site_name} clear-cache
bench build
```

### Check Logs
```bash
tail -f ~/frappe-bench/logs/bench.log
```

### Check Browser Console
- Press F12
- Go to Console tab
- Look for JavaScript errors
- Errors will give clues about what's wrong

---

## Success Indicators ✅

You know installation is successful when:

1. ✅ All 5 DocTypes exist
2. ✅ Custom fields visible in standard forms
3. ✅ 6 roles created
4. ✅ C4agent workspace visible
5. ✅ "Create > Import Shipment" button appears on submitted PO
6. ✅ Can create shipment from button
7. ✅ Fields auto-populate from PO
8. ✅ Can change statuses
9. ✅ Can create containers
10. ✅ Custom fields fetch from shipment

---

## Next Steps After Verification

Once all checks pass:
1. Assign users to Import roles
2. Configure C4agent Settings
3. Follow [TESTING_GUIDE_PHASE1.md](TESTING_GUIDE_PHASE1.md) for full testing

---

**Use this checklist to verify successful installation!** ✅
