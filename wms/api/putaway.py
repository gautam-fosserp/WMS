import frappe
from frappe import _


@frappe.whitelist()
def get_suggested_putaway_bin(item_code, warehouse, qty=1, allow_partial=False, exclude_reserved=None):
    qty = frappe.utils.flt(qty)
    exclude_reserved = exclude_reserved or {}

    existing = frappe.get_all(
        "WMS Bin Location",
        filters={"warehouse": warehouse, "current_item": item_code, "status": "Occupied"},
        fields=["name", "bin_id", "aisle", "rack", "shelf", "qty_in_bin", "max_capacity"],
    )
    best_partial = None
    for bin_row in existing:
        effective_qty_in_bin = (bin_row.qty_in_bin or 0) + exclude_reserved.get(bin_row.name, 0)
        remaining = (bin_row.max_capacity - effective_qty_in_bin) if bin_row.max_capacity else qty
        if not bin_row.max_capacity or remaining >= qty:
            bin_row["message"] = _("Matching inventory found. Consolidate here.")
            return bin_row
        if allow_partial and remaining > 0 and (not best_partial or remaining > best_partial["_remaining"]):
            bin_row["_remaining"] = remaining
            best_partial = bin_row

    vacant = frappe.get_all(
        "WMS Bin Location",
        filters={"warehouse": warehouse, "status": "Vacant"},
        fields=["name", "bin_id", "aisle", "rack", "shelf", "max_capacity"],
    )
    for bin_row in vacant:
        effective_reserved = exclude_reserved.get(bin_row.name, 0)
        remaining = (bin_row.max_capacity - effective_reserved) if bin_row.max_capacity else qty
        if not bin_row.max_capacity or remaining >= qty:
            bin_row["message"] = _("Suggested open bin.")
            return bin_row
        if allow_partial and remaining > 0 and (not best_partial or remaining > best_partial["_remaining"]):
            bin_row["_remaining"] = remaining
            best_partial = bin_row

    if allow_partial and best_partial:
        best_partial["message"] = _("Partial space available. Consolidate here.")
        return best_partial

    return {"name": None, "message": _("No available bin with sufficient capacity. Assign manually.")}


@frappe.whitelist()
def confirm_putaway(task_name, scanned_bin_id):
    task = frappe.get_doc("WMS Task", task_name)

    if not task.target_bin:
        frappe.throw(_("This task has no assigned bin yet. Cannot confirm putaway."))

    bin_doc = frappe.get_doc("WMS Bin Location", task.target_bin)
    if bin_doc.bin_id != scanned_bin_id:
        frappe.throw(_("Scanned bin does not match assigned bin. Expected {0}").format(bin_doc.bin_id))

    new_qty = (bin_doc.qty_in_bin or 0) + task.qty
    if bin_doc.max_capacity and new_qty > bin_doc.max_capacity:
        frappe.throw(
            _("Bin {0} capacity exceeded. Max: {1}, Current: {2}, Trying to add: {3}")
            .format(bin_doc.bin_id, bin_doc.max_capacity, bin_doc.qty_in_bin or 0, task.qty)
        )

    bin_doc.status = "Occupied"
    bin_doc.current_item = task.item_code
    bin_doc.qty_in_bin = new_qty
    bin_doc.save(ignore_permissions=True)

    task.status = "Completed"
    task.completed_at = frappe.utils.now_datetime()
    task.save(ignore_permissions=True)

    frappe.db.commit()
    return {"success": True, "message": _("Putaway confirmed at {0}").format(bin_doc.bin_id)}


@frappe.whitelist()
def retry_bin_suggestion(task_name):
    """
    Re-attempts bin assignment for a task stuck without a target_bin
    (e.g. created before any WMS Bin Location existed for that warehouse).
    """
    task = frappe.get_doc("WMS Task", task_name)

    if task.target_bin:
        return {"success": False, "message": _("Task already has a target bin assigned.")}

    if task.status != "Open":
        return {"success": False, "message": _("Only Open tasks can be retried.")}

    suggestion = get_suggested_putaway_bin(task.item_code, task.warehouse, qty=task.qty)
    if not suggestion.get("name"):
        return {"success": False, "message": _("Still no bin available. Create one first.")}

    task.target_bin = suggestion["name"]
    task.save(ignore_permissions=True)
    frappe.db.commit()

    return {"success": True, "message": _("Bin {0} assigned.").format(suggestion["bin_id"])}


def create_putaway_tasks(doc, method):
    for item in doc.items:
        remaining_qty = item.qty
        reserved_in_this_run = {}

        while remaining_qty > 0:
            suggestion = get_suggested_putaway_bin(
                item.item_code, item.warehouse, qty=remaining_qty, allow_partial=True,
                exclude_reserved=reserved_in_this_run
            )

            if not suggestion.get("name"):
                # No bin has room for what's left — don't block the receipt.
                # Create an exception task instead so a supervisor can resolve it.
                frappe.get_doc({
                    "doctype": "WMS Task",
                    "company": doc.company,
                    "task_type": "Putaway",
                    "reference_doctype": "Purchase Receipt",
                    "reference_name": doc.name,
                    "item_code": item.item_code,
                    "qty": remaining_qty,
                    "warehouse": item.warehouse,
                    "status": "Exception",
                    "exception_reason": "Bin Full",
                    "exception_notes": _("No bin had room during receipt processing."),
                    "exception_reported_by": frappe.session.user,
                    "exception_reported_at": frappe.utils.now_datetime(),
                }).insert(ignore_permissions=True)
                break

            bin_doc = frappe.db.get_value(
                "WMS Bin Location", suggestion["name"],
                ["max_capacity", "qty_in_bin"], as_dict=True
            )
            already_reserved = reserved_in_this_run.get(suggestion["name"], 0)
            actual_qty_in_bin = (bin_doc.qty_in_bin or 0) + already_reserved
            available_space = (bin_doc.max_capacity - actual_qty_in_bin) if bin_doc.max_capacity else remaining_qty
            qty_for_this_bin = min(remaining_qty, available_space)

            frappe.get_doc({
                "doctype": "WMS Task",
                "company": doc.company,
                "task_type": "Putaway",
                "reference_doctype": "Purchase Receipt",
                "reference_name": doc.name,
                "item_code": item.item_code,
                "qty": qty_for_this_bin,
                "target_bin": suggestion["name"],
                "warehouse": item.warehouse,
                "status": "Open",
            }).insert(ignore_permissions=True)

            reserved_in_this_run[suggestion["name"]] = already_reserved + qty_for_this_bin
            remaining_qty -= qty_for_this_bin


@frappe.whitelist()
def report_exception(task_name, exception_reason, exception_notes=None):
    """
    Called when a worker can't complete a task as assigned —
    bin is full, damaged, wrong item, etc. Pulls the task out of
    the normal open queue and flags it for a supervisor to resolve.
    """
    task = frappe.get_doc("WMS Task", task_name)

    if task.status == "Completed":
        frappe.throw(_("This task is already completed."))

    task.status = "Exception"
    task.exception_reason = exception_reason
    task.exception_notes = exception_notes
    task.exception_reported_by = frappe.session.user
    task.exception_reported_at = frappe.utils.now_datetime()
    task.save(ignore_permissions=True)

    # If the bin itself was reported full/damaged, mark it so it's not
    # suggested again until a supervisor reviews it
    if exception_reason in ("Bin Full", "Bin Damaged or Missing") and task.target_bin:
        frappe.db.set_value("WMS Bin Location", task.target_bin, "status", "Blocked")

    frappe.db.commit()
    return {"success": True, "message": _("Exception reported. A supervisor will review this task.")}


@frappe.whitelist()
def resolve_exception(task_name, reassign_new_bin=True):
    require_supervisor()
    task = frappe.get_doc("WMS Task", task_name)

    if task.status != "Exception":
        frappe.throw(_("Only tasks with status 'Exception' can be resolved this way."))

    task.target_bin = None
    task.status = "Open"
    task.exception_reason = None
    task.exception_notes = None
    task.save(ignore_permissions=True)

    if reassign_new_bin:
        result = retry_bin_suggestion(task.name)
        return result

    frappe.db.commit()
    return {"success": True, "message": _("Task reopened for manual bin assignment.")}


@frappe.whitelist()
def get_exception_tasks(warehouse=None):
    require_supervisor()
    filters = {"status": "Exception"}
    if warehouse:
        filters["warehouse"] = warehouse
    return frappe.get_all("WMS Task", filters=filters,
        fields=["name", "item_code", "qty", "target_bin", "warehouse",
                "exception_reason", "exception_notes", "exception_reported_by", "exception_reported_at"])


def require_supervisor():
    if "WMS Supervisor" not in frappe.get_roles(frappe.session.user):
        frappe.throw(_("You don't have permission to access this."), frappe.PermissionError)


@frappe.whitelist()
def get_bin_capacity_info(bin_name):
    """
    Returns current fill level for a bin, so the frontend can show
    the worker how much room is left before they scan/confirm.
    """
    bin_doc = frappe.db.get_value(
        "WMS Bin Location", bin_name,
        ["bin_id", "qty_in_bin", "max_capacity"],
        as_dict=True
    )
    if not bin_doc:
        return None

    qty_in_bin = bin_doc.qty_in_bin or 0
    max_capacity = bin_doc.max_capacity or 0

    return {
        "bin_id": bin_doc.bin_id,
        "qty_in_bin": qty_in_bin,
        "max_capacity": max_capacity,
        "remaining": (max_capacity - qty_in_bin) if max_capacity else None,
    }