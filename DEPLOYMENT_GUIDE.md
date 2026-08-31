# QUICK DEPLOYMENT & FIX GUIDE

## ⚠️ Important: After Installing App, Run These Commands

After `bench install-app c4agent`, you **MUST** run these commands to activate the custom button:

```bash
# Clear cache to reload custom scripts
bench --site {site_name} clear-cache

# Rebuild the app bundle
bench build

# Optional: Restart bench
bench restart
```

---

## Why This Is Needed

The custom "Create > Import Shipment" button on Purchase Order requires:
1. Cache to be cleared so new JS files are loaded
2. App bundle rebuilt
3. Browser cache cleared (refresh Ctrl+F5)

---

## Step-by-Step Deployment

### Step 1: Install C4agent App
```bash
cd /path/to/frappe-bench
bench install-app c4agent
```

### Step 2: Clear Cache & Rebuild
```bash
bench --site {site_name} clear-cache
bench build
```

### Step 3: Hard Refresh Browser
- Open ERPNext in browser
- Press **Ctrl + Shift + Delete** (or Cmd + Shift + Delete on Mac)
- Clear browsing data > JavaScript/CSS files
- Or simply do **Ctrl + F5** for hard refresh

### Step 4: Test the Button

1. Go to **Buying > Purchase Order**
2. Open any **submitted** PO
3. Click **"Create"** button dropdown
4. Look for **"Import Shipment"** option
5. Click it to create shipment from PO

---

## If Button Still Doesn't Appear

### Option 1: Check Browser Console
1. Press **F12** to open Developer Tools
2. Go to **Console** tab
3. Check for JavaScript errors
4. If you see errors, screenshot and report

### Option 2: Clear Everything
```bash
# Remove all caches
bench --site {site_name} clear-cache
rm -rf apps/c4agent/.parcel-cache
bench build
bench restart
```

### Option 3: Reload Page
1. Close ERPNext tab
2. Restart browser
3. Log in again
4. Try the button

---

## File Structure (Corrected)

The custom button is now located at:
```
c4agent/
├── public/
│   └── js/
│       └── purchase_order.js  ← Custom button script
└── hooks.py                   ← References the file above
```

This is the standard Frappe pattern for custom doctype scripts.

---

## What the Button Does

When clicked on a **submitted** Purchase Order:

1. **Calls**: `c4agent.c4agent.services.shipment.create_import_shipment_from_po`
2. **Creates**: New Import Shipment document
3. **Auto-populates**:
   - Company (from PO)
   - Supplier (from PO)
   - Currency (from PO)
   - All items with quantities and rates
4. **Opens**: New shipment form for you to add shipping details

---

## Testing After Deployment

```bash
# Run tests
bench --site {site_name} run-tests --app c4agent --verbose
```

Expected: All tests pass

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Button not visible | Hard refresh (Ctrl+F5), clear browser cache |
| "Import Shipment not found" error | Run `bench install-app c4agent` again |
| Method not found error | Check that `services/shipment.py` exists and is readable |
| JavaScript errors in console | Run `bench build` and restart |

---

## Next: Testing Phase

After successful deployment, follow [TESTING_GUIDE_PHASE1.md](TESTING_GUIDE_PHASE1.md) to verify all features work correctly.

---

**Ready to deploy!** 🚀
