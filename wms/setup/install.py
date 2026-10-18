import frappe

def set_default_settings():
    """Seed WMS Settings defaults without overwriting existing values."""
    meta = frappe.get_meta("WMS Settings")
    for df in meta.fields:
        if not df.default:
            continue
        current = frappe.db.get_single_value("WMS Settings", df.fieldname)
        if current in (None, ""):
            frappe.db.set_single_value("WMS Settings", df.fieldname, df.default)