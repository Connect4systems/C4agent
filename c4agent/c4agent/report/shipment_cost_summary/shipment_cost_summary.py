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
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Ocean Freight' then e.base_amount else 0 end),0) ocean_freight,
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Customs Duty' then e.base_amount else 0 end),0) customs_duty,
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Customs Broker' then e.base_amount else 0 end),0) broker,
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Port Charges' then e.base_amount else 0 end),0) port,
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Storage' then e.base_amount else 0 end),0) storage,
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Demurrage' then e.base_amount else 0 end),0) demurrage,
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Transportation' then e.base_amount else 0 end),0) transportation,
		coalesce(sum(case when e.docstatus=1 and e.expense_type='Marine Insurance' then e.base_amount else 0 end),0) insurance,
		coalesce(sum(case when e.docstatus=1 and e.expense_type not in ('Ocean Freight','Customs Duty','Customs Broker','Port Charges','Storage','Demurrage','Transportation','Marine Insurance') then e.base_amount else 0 end),0) other,
		coalesce(sum(case when e.docstatus=1 then e.base_amount else 0 end),0) total_expenses,
		coalesce(sum(case when e.docstatus=1 and e.landed_cost_allocated=1 then e.base_amount else 0 end),0) allocated_cost
		from `tabImport Shipment` s left join `tabImport Expense` e on e.import_shipment=s.name
		{where} group by s.name, s.supplier, s.shipment_status, s.po_value order by s.creation desc""", values, as_dict=True)
	columns = [
		{"label":"Shipment","fieldname":"name","fieldtype":"Link","options":"Import Shipment","width":150},
		{"label":"Supplier","fieldname":"supplier","fieldtype":"Link","options":"Supplier","width":180},
		{"label":"Status","fieldname":"shipment_status","width":140},
		{"label":"PO Value","fieldname":"po_value","fieldtype":"Currency","width":130},
		{"label":"Ocean Freight","fieldname":"ocean_freight","fieldtype":"Currency","width":120},
		{"label":"Customs Duty","fieldname":"customs_duty","fieldtype":"Currency","width":120},
		{"label":"Broker","fieldname":"broker","fieldtype":"Currency","width":100},
		{"label":"Port","fieldname":"port","fieldtype":"Currency","width":100},
		{"label":"Storage","fieldname":"storage","fieldtype":"Currency","width":100},
		{"label":"Demurrage","fieldname":"demurrage","fieldtype":"Currency","width":110},
		{"label":"Transportation","fieldname":"transportation","fieldtype":"Currency","width":120},
		{"label":"Insurance","fieldname":"insurance","fieldtype":"Currency","width":100},
		{"label":"Other","fieldname":"other","fieldtype":"Currency","width":100},
		{"label":"Import Expenses","fieldname":"total_expenses","fieldtype":"Currency","width":140},
		{"label":"Allocated Cost","fieldname":"allocated_cost","fieldtype":"Currency","width":140},
	]
	return columns, data
