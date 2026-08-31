import frappe


def execute(filters=None):
	filters = filters or {}
	conditions, values = [], {}
	for filter_name, column in (("import_shipment", "import_shipment"), ("container", "name"), ("container_type", "container_type"), ("container_status", "container_status")):
		if filters.get(filter_name):
			conditions.append(f"c.{column}=%({filter_name})s")
			values[filter_name] = filters[filter_name]
	where = "where " + " and ".join(conditions) if conditions else ""
	data = frappe.db.sql(f"""select c.name, c.import_shipment, c.container_type, c.packages, c.gross_weight, c.cbm,
		c.freight_cost, c.port_cost, c.storage_cost, c.demurrage_cost, c.transportation_cost, c.other_cost, c.total_container_cost
		from `tabImport Container` c {where} order by c.import_shipment desc""", values, as_dict=True)
	columns = [
		{"label":"Container","fieldname":"name","fieldtype":"Link","options":"Import Container","width":160},
		{"label":"Shipment","fieldname":"import_shipment","fieldtype":"Link","options":"Import Shipment","width":150},
		{"label":"Type","fieldname":"container_type","width":100},
		{"label":"Packages","fieldname":"packages","fieldtype":"Int","width":90},
		{"label":"Gross Weight","fieldname":"gross_weight","fieldtype":"Float","width":120},
		{"label":"CBM","fieldname":"cbm","fieldtype":"Float","width":90},
		{"label":"Freight","fieldname":"freight_cost","fieldtype":"Currency","width":110},
		{"label":"Port","fieldname":"port_cost","fieldtype":"Currency","width":110},
		{"label":"Storage","fieldname":"storage_cost","fieldtype":"Currency","width":110},
		{"label":"Demurrage","fieldname":"demurrage_cost","fieldtype":"Currency","width":110},
		{"label":"Transportation","fieldname":"transportation_cost","fieldtype":"Currency","width":120},
		{"label":"Other","fieldname":"other_cost","fieldtype":"Currency","width":100},
		{"label":"Total Cost","fieldname":"total_container_cost","fieldtype":"Currency","width":130},
	]
	return columns, data
