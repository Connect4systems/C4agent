from frappe import _


def get_data():
	return {
		"fieldname": "custom_import_shipment",
		"non_standard_fieldnames": {
			"Import Container": "import_shipment",
			"Customs Declaration": "import_shipment",
			"Import Expense": "import_shipment",
			"Sinosure Coverage": "import_shipment",
		},
		"transactions": [
			{"label": _("Operations"), "items": ["Import Container", "Customs Declaration"]},
			{"label": _("Finance"), "items": ["Purchase Invoice", "Import Expense", "Sinosure Coverage"]},
			{"label": _("Stock and Valuation"), "items": ["Purchase Receipt", "Landed Cost Voucher"]},
		],
	}
