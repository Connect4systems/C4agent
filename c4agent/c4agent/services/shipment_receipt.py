import frappe
from frappe.utils import flt


@frappe.whitelist()
def make_purchase_receipt(source_name, target_doc=None):
	"""Open an unsaved standard PO receipt limited to this shipment's balance."""
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt as map_po

	shipment = frappe.get_doc("Import Shipment", source_name)
	shipment.check_permission("read")
	if not frappe.has_permission("Purchase Receipt", "create"):
		frappe.throw("Not permitted to create a Purchase Receipt", frappe.PermissionError)
	if shipment.shipment_status not in ("Cleared", "Received"):
		frappe.throw("Shipment must be Cleared before creating a Purchase Receipt")
	po = frappe.get_doc("Purchase Order", shipment.purchase_order)
	po.check_permission("read")
	if po.docstatus != 1 or po.status in ("Closed", "Cancelled", "On Hold"):
		frappe.throw("Purchase Order must be submitted and open for receiving")
	if po.company != shipment.company or po.supplier != shipment.supplier:
		frappe.throw("Purchase Order company and supplier must match the shipment")
	remaining = {}
	for row in shipment.items:
		remaining[row.purchase_order_item] = remaining.get(row.purchase_order_item, 0) + flt(row.shipped_qty)
	# Read submitted receipts directly, including negative quantities from returns.
	for row in frappe.db.sql("""
		select i.purchase_order_item, sum(i.qty) as qty
		from `tabPurchase Receipt Item` i
		inner join `tabPurchase Receipt` r on r.name=i.parent
		where r.custom_import_shipment=%s and r.docstatus=1
		group by i.purchase_order_item
	""", source_name, as_dict=True):
		remaining[row.purchase_order_item] = remaining.get(row.purchase_order_item, 0) - flt(row.qty)
	if not any(qty > 0 for qty in remaining.values()):
		frappe.throw("No unreceived shipment quantities remain. Check Shipped Qty on the shipment items.")
	# Always start a fresh draft; do not mix a second shipment into an existing receipt.
	receipt = map_po(po.name)
	receipt.custom_import_shipment = shipment.name
	items = []
	for row in receipt.items:
		qty = min(flt(row.qty), remaining.get(row.purchase_order_item, 0))
		if qty <= 0:
			continue
		row.qty = qty
		row.received_qty = qty
		row.stock_qty = qty * flt(row.conversion_factor or 1)
		if shipment.final_destination:
			row.warehouse = shipment.final_destination
		items.append(row)
	if not items:
		frappe.throw("No shipment items remain receivable on this Purchase Order")
	receipt.set("items", items)
	if shipment.final_destination:
		receipt.set_warehouse = shipment.final_destination
	receipt.run_method("calculate_taxes_and_totals")
	return receipt
