import frappe


def execute(filters=None):
	filters = filters or {}
	conditions, values = [], {}
	for field in ("company", "supplier"):
		if filters.get(field):
			conditions.append(f"s.{field}=%({field})s")
			values[field] = filters[field]
	if filters.get("shipment"):
		conditions.append("s.name=%(shipment)s")
		values["shipment"] = filters["shipment"]
	if filters.get("from_date"):
		conditions.append("date(s.creation)>=%(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("date(s.creation)<=%(to_date)s")
		values["to_date"] = filters["to_date"]
	where = "where " + " and ".join(conditions) if conditions else ""
	data = frappe.db.sql(f"""select s.name, s.supplier, s.shipment_status, s.po_value,
		coalesce(sum(case when e.docstatus=1 and coalesce(t.type, 'Import Expenses')='Import Expenses'
			then e.base_amount else 0 end),0) import_expenses,
		coalesce(sum(case when e.docstatus=1 and t.type='Customs Declaration'
			then e.base_amount else 0 end),0) customs_declaration,
		coalesce(sum(case when e.docstatus=1 then e.base_amount else 0 end),0) total_expenses,
		coalesce(sum(case when e.docstatus=1 and e.landed_cost_allocated=1 then e.base_amount else 0 end),0) allocated_cost
		from `tabImport Shipment` s
		left join `tabImport Expense` e on e.import_shipment=s.name
		left join `tabImport Expense Type` t on t.name=e.expense_type
		{where} group by s.name, s.supplier, s.shipment_status, s.po_value order by s.creation desc""", values, as_dict=True)
	columns = [
		{"label":"Shipment","fieldname":"name","fieldtype":"Link","options":"Import Shipment","width":150},
		{"label":"Supplier","fieldname":"supplier","fieldtype":"Link","options":"Supplier","width":180},
		{"label":"Status","fieldname":"shipment_status","width":140},
		{"label":"PO Value","fieldname":"po_value","fieldtype":"Currency","width":130},
		{"label":"Import Expenses","fieldname":"import_expenses","fieldtype":"Currency","width":140},
		{"label":"Customs Declaration","fieldname":"customs_declaration","fieldtype":"Currency","width":145},
		{"label":"Total Expenses","fieldname":"total_expenses","fieldtype":"Currency","width":140},
		{"label":"Allocated Cost","fieldname":"allocated_cost","fieldtype":"Currency","width":140},
	]
	return columns, data
