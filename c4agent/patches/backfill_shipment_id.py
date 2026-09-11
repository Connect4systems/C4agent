import frappe


def execute():
	"""Populate the new naming field without renaming existing shipments."""
	shipment = frappe.qb.DocType("Import Shipment")
	(
		frappe.qb.update(shipment)
		.set(shipment.shipment_id, shipment.name)
		.where(shipment.shipment_id.isnull() | (shipment.shipment_id == ""))
	).run()
