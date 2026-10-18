import frappe

from wms.api.api import get_current_user_info, get_pending_tasks
from wms.api.putaway import get_exception_tasks
from wms.api.receiving import get_receiving_config


@frappe.whitelist()
def get_home_summary():
    info = get_current_user_info()
    cfg = get_receiving_config()
    is_supervisor = bool(info.get("is_supervisor"))

    return {
        "user": info,
        "receiving_mode": (cfg or {}).get("receiving_mode") or "Standard ERPNext Only",
        "pending_count": len(get_pending_tasks() or []),
        "exception_count": len(get_exception_tasks() or []) if is_supervisor else 0,
    }