import frappe
from frappe import _

@frappe.whitelist()
def get_pending_tasks(warehouse=None):
    user_companies = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Company"},
        pluck="for_value"
    )
    filters = {"status": "Open"}
    if user_companies:
        filters["company"] = ["in", user_companies]
    if warehouse:
        filters["warehouse"] = warehouse

    return frappe.get_all(
        "WMS Task",
        filters=filters,
        fields=["name", "task_type", "item_code", "qty", "target_bin", "warehouse"]
    )

@frappe.whitelist()
def get_current_user_info():
    return {
        "user": frappe.session.user,
        "is_supervisor": "WMS Supervisor" in frappe.get_roles(frappe.session.user),
    }