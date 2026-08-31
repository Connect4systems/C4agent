import frappe


def execute(filters=None):
	filters = filters or {}
	conditions, values = [], {}
	for field in ("company", "supplier", "coverage_status"):
		if filters.get(field):
			conditions.append(f"c.{field}=%({field})s")
			values[field] = filters[field]
	if filters.get("expiry_to"):
		conditions.append("c.coverage_expiry_date<=%(expiry_to)s")
		values["expiry_to"] = filters["expiry_to"]
	where = "where " + " and ".join(conditions) if conditions else ""
	columns = [
		{"label":"Coverage","fieldname":"name","fieldtype":"Link","options":"Sinosure Coverage","width":150},
		{"label":"Supplier","fieldname":"supplier","fieldtype":"Link","options":"Supplier","width":180},
		{"label":"Policy","fieldname":"policy_number","fieldtype":"Data","width":130},
		{"label":"Shipment","fieldname":"import_shipment","fieldtype":"Link","options":"Import Shipment","width":150},
		{"label":"Status","fieldname":"coverage_status","width":100},
		{"label":"Currency","fieldname":"coverage_currency","fieldtype":"Link","options":"Currency","width":90},
		{"label":"Approved Limit","fieldname":"approved_limit","fieldtype":"Currency","options":"coverage_currency","width":130},
		{"label":"Previous Exposure","fieldname":"opening_or_previous_exposure","fieldtype":"Currency","options":"coverage_currency","width":130},
		{"label":"Shipment Exposure","fieldname":"current_shipment_exposure","fieldtype":"Currency","options":"coverage_currency","width":130},
		{"label":"Remaining","fieldname":"remaining_limit","fieldtype":"Currency","options":"coverage_currency","width":130},
		{"label":"Expiry","fieldname":"coverage_expiry_date","fieldtype":"Date","width":100},
	]
	data = frappe.db.sql(f"""select c.name, c.supplier, c.policy_number, c.import_shipment, c.coverage_status, c.coverage_currency,
		c.approved_limit, c.opening_or_previous_exposure, c.current_shipment_exposure,
		c.remaining_limit, c.coverage_expiry_date from `tabSinosure Coverage` c
		{where} order by c.coverage_expiry_date asc""", values, as_dict=True)
	return columns, data
