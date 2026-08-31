# Copyright (c) 2026, Connect 4 systems and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_c4agent_custom_fields():
	"""Create custom fields on standard doctypes"""
	
	custom_fields = {
		"Supplier": [
			{
				"fieldname": "custom_is_foreign_supplier",
				"fieldtype": "Check",
				"label": "Is Foreign Supplier",
				"insert_after": "supplier_type"
			},
			{
				"fieldname": "custom_is_shipping_agent",
				"fieldtype": "Check",
				"label": "Is Shipping Agent",
				"insert_after": "custom_is_foreign_supplier"
			},
			{
				"fieldname": "custom_is_customs_broker",
				"fieldtype": "Check",
				"label": "Is Customs Broker",
				"insert_after": "custom_is_shipping_agent"
			},
			{
				"fieldname": "custom_is_logistics_provider",
				"fieldtype": "Check",
				"label": "Is Logistics Provider",
				"insert_after": "custom_is_customs_broker"
			},
		],
		"Purchase Invoice": [
			{
				"fieldname": "custom_import_info_section",
				"fieldtype": "Section Break",
				"label": "Import Information",
				"insert_after": "remarks"
			},
			{
				"fieldname": "custom_import_shipment",
				"fieldtype": "Link",
				"label": "Import Shipment",
				"options": "Import Shipment",
				"insert_after": "custom_import_info_section"
			},
			{
				"fieldname": "custom_acid_number",
				"fieldtype": "Data",
				"label": "ACID Number",
				"insert_after": "custom_import_shipment",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.acid_number"
			},
			{
				"fieldname": "custom_bill_of_lading",
				"fieldtype": "Data",
				"label": "Bill of Lading",
				"insert_after": "custom_acid_number",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.bill_of_lading"
			},
			{
				"fieldname": "custom_shipping_line",
				"fieldtype": "Link",
				"label": "Shipping Line",
				"options": "Shipping Line",
				"insert_after": "custom_bill_of_lading",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.shipping_line"
			},
			{
				"fieldname": "custom_vessel",
				"fieldtype": "Data",
				"label": "Vessel",
				"insert_after": "custom_shipping_line",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.vessel"
			},
			{
				"fieldname": "custom_voyage",
				"fieldtype": "Data",
				"label": "Voyage",
				"insert_after": "custom_vessel",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.voyage"
			},
			{
				"fieldname": "custom_etd",
				"fieldtype": "Date",
				"label": "ETD",
				"insert_after": "custom_voyage",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.etd"
			},
			{
				"fieldname": "custom_eta",
				"fieldtype": "Date",
				"label": "ETA",
				"insert_after": "custom_etd",
				"read_only": 1,
				"fetch_from": "custom_import_shipment.eta"
			},
		],
		"Purchase Receipt": [
			{
				"fieldname": "custom_import_shipment",
				"fieldtype": "Link",
				"label": "Import Shipment",
				"options": "Import Shipment",
				"insert_after": "remarks"
			},
		],
		"Purchase Receipt Item": [
			{
				"fieldname": "custom_import_container",
				"fieldtype": "Link",
				"label": "Import Container",
				"options": "Import Container",
				"insert_after": "price_list_rate"
			},
		],
		"Landed Cost Voucher": [
			{
				"fieldname": "custom_import_shipment",
				"fieldtype": "Link",
				"label": "Import Shipment",
				"options": "Import Shipment",
				"insert_after": "remarks"
			},
		],
		"Item": [
			{
				"fieldname": "custom_wattage",
				"fieldtype": "Float",
				"label": "Wattage (for Solar Panels)",
				"precision": 2,
				"insert_after": "weight_uom"
			},
		],
	}
	
	create_custom_fields(custom_fields, ignore_validate=True)
	frappe.db.commit()


def setup_c4agent_roles():
	"""Create roles for C4agent"""
	
	roles_data = [
		{
			"role_name": "Import User",
			"doctype": "Role"
		},
		{
			"role_name": "Import Manager",
			"doctype": "Role"
		},
		{
			"role_name": "Customs User",
			"doctype": "Role"
		},
		{
			"role_name": "Customs Manager",
			"doctype": "Role"
		},
		{
			"role_name": "Finance User",
			"doctype": "Role"
		},
		{
			"role_name": "Finance Manager",
			"doctype": "Role"
		},
	]
	
	for role_data in roles_data:
		role_name = role_data["role_name"]
		if not frappe.db.exists("Role", role_name):
			role = frappe.new_doc("Role")
			role.role_name = role_name
			role.insert(ignore_permissions=True)
			frappe.db.commit()
