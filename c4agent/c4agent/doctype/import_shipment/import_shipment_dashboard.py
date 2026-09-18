from frappe import _


def get_data():
	return {
		"fieldname": "custom_import_shipment",
		"non_standard_fieldnames": {
			"Import Expense": "import_shipment",
			"Sinosure Coverage": "import_shipment",
		},
		"transactions": [
			{"label": _("Finance"), "items": ["Purchase Invoice", "Import Expense", "Sinosure Coverage"]},
			{"label": _("Stock and Valuation"), "items": ["Purchase Receipt", "Landed Cost Voucher"]},
		],
	}
