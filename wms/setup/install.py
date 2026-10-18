import frappe


def before_install():
    """
    Runs BEFORE Frappe migrates wms DocTypes and BEFORE init_singles() saves
    the WMS Settings singleton. We must create the Role here so the install
    doesn't crash on Link validation.
    """
    _ensure_wms_supervisor_role()


def set_default_settings():
    """
    Runs on after_install and after_migrate.
    Seeds WMS Settings defaults without overwriting existing values.
    """
    _ensure_wms_supervisor_role()
    
    meta = frappe.get_meta("WMS Settings")
    for df in meta.fields:
        if not df.default:
            continue
        current = frappe.db.get_single_value("WMS Settings", df.fieldname)
        if current in (None, ""):
            frappe.db.set_single_value("WMS Settings", df.fieldname, df.default)


def _ensure_wms_supervisor_role():
    """Helper to create the required Role if it doesn't exist."""
    role_name = "WMS Supervisor"
    if frappe.db.exists("Role", role_name):
        return
    role = frappe.new_doc("Role")
    role.role_name = role_name
    role.desk_access = 1
    role.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"Created Role: {role_name}")