from frappe import _


def get_data(data):
	"""Add all shipments linked to this PO without replacing ERPNext connections."""
	data.setdefault("non_standard_fieldnames", {})["Import Shipment"] = "purchase_order"
	transactions = data.setdefault("transactions", [])
	if not any("Import Shipment" in group.get("items", []) for group in transactions):
		transactions.append({"label": _("Imports"), "items": ["Import Shipment"]})
	return data
