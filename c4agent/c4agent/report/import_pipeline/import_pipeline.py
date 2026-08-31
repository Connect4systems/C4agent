import frappe
from frappe.utils import add_days, getdate, nowdate


def execute(filters=None):
	filters = filters or {}
	query_filters = {key: filters[key] for key in ("company", "supplier", "shipment_status", "shipping_line", "purchase_order") if filters.get(key)}
	if filters.get("from_eta"):
		query_filters["eta"] = (">=", filters["from_eta"])
	if filters.get("to_eta"):
		query_filters["eta"] = ("between", [filters.get("from_eta") or "1900-01-01", filters["to_eta"]])
	columns = [
		{"label":"Shipment","fieldname":"name","fieldtype":"Link","options":"Import Shipment","width":150},
		{"label":"Supplier","fieldname":"supplier","fieldtype":"Link","options":"Supplier","width":180},
		{"label":"Purchase Order","fieldname":"purchase_order","fieldtype":"Link","options":"Purchase Order","width":150},
		{"label":"Shipping Line","fieldname":"shipping_line","fieldtype":"Link","options":"Shipping Line","width":140},
		{"label":"B/L","fieldname":"bill_of_lading","fieldtype":"Data","width":130},
		{"label":"Containers","fieldname":"container_count","fieldtype":"Int","width":85},
		{"label":"Status","fieldname":"shipment_status","fieldtype":"Data","width":150},
		{"label":"ETD","fieldname":"etd","fieldtype":"Date","width":100},
		{"label":"ETA","fieldname":"eta","fieldtype":"Date","width":100},
		{"label":"Actual Arrival","fieldname":"actual_arrival_date","fieldtype":"Date","width":110},
		{"label":"ACID","fieldname":"acid_number","fieldtype":"Data","width":150},
		{"label":"PO Value","fieldname":"po_value","fieldtype":"Currency","width":120},
		{"label":"Import Expenses","fieldname":"total_import_expenses","fieldtype":"Currency","width":130},
		{"label":"Landed Cost","fieldname":"total_landed_cost","fieldtype":"Currency","width":120},
		{"label":"Indicator","fieldname":"indicator","fieldtype":"Data","width":120},
	]
	fields = [c["fieldname"] for c in columns if c["fieldname"] != "indicator"]
	data = frappe.get_all("Import Shipment", filters=query_filters, fields=fields, order_by="eta asc")
	today = getdate(nowdate())
	for row in data:
		row.indicator = ""
		if row.shipment_status == "In Transit" and row.eta and not row.actual_arrival_date:
			if getdate(row.eta) < today:
				row.indicator = "Delayed"
			elif getdate(row.eta) <= getdate(add_days(today, 3)):
				row.indicator = "Arriving Soon"
		if row.shipment_status in ("Arrived", "Under Customs Clearance"):
			row.indicator = "Customs Pending"
	return columns, data
