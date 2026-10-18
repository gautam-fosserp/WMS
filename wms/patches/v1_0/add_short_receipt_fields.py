import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Purchase Order Item": [
            {
                "fieldname": "wms_short_reason",
                "label": "WMS Short Reason",
                "fieldtype": "Select",
                "options": "\nSupplier Short Shipped\nLost in Transit\nBackordered\nCancelled by Supplier\nOther",
                "insert_after": "received_qty",
                "no_copy": 1,
                "translatable": 0,
                "description": "Set by WMS Receiving Screen when received qty is less than ordered qty.",
            },
            {
                "fieldname": "wms_short_notes",
                "label": "WMS Short Notes",
                "fieldtype": "Small Text",
                "insert_after": "wms_short_reason",
                "no_copy": 1,
            },
            {
                "fieldname": "wms_short_captured_at",
                "label": "WMS Short Captured At",
                "fieldtype": "Datetime",
                "insert_after": "wms_short_notes",
                "read_only": 1,
                "no_copy": 1,
                "print_hide": 1,
            },
            {
                "fieldname": "wms_short_captured_by",
                "label": "WMS Short Captured By",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "wms_short_captured_at",
                "read_only": 1,
                "no_copy": 1,
                "print_hide": 1,
            },
        ]
    })