import frappe
from frappe import _
from frappe.utils import get_url_to_form
from wms.wms.doctype.wms_settings.wms_settings import get_settings


def _open_reserved(bin_name):
    """Qty promised to Open putaway tasks that haven't been confirmed yet."""
    return frappe.db.sql(
        """SELECT COALESCE(SUM(qty), 0) FROM `tabWMS Task`
           WHERE target_bin = %s AND status = 'Open' AND task_type = 'Putaway'""",
        bin_name,
    )[0][0]


def _free_space(bin_name, qty_in_bin, max_capacity):
    """None means unlimited."""
    if not max_capacity:
        return None
    return max_capacity - (qty_in_bin or 0) - _open_reserved(bin_name)

@frappe.whitelist()
def get_suggested_putaway_bin(item_code, warehouse, qty=1, allow_partial=False):
    settings = get_settings()
    excluded_types = settings["excluded_bin_types"]
    qty = frappe.utils.flt(qty)

    or_filters = []
    if excluded_types:
        or_filters = [
            ["bin_type", "not in", excluded_types],
            ["bin_type", "is", "not set"],
        ]

    best_partial = None

    def consider(bin_row, free, message):
        """Return bin if it fits fully, else remember it as best partial."""
        nonlocal best_partial
        if free is None or free >= qty:
            bin_row["message"] = message
            return bin_row
        if allow_partial and free > 0 and (not best_partial or free > best_partial["_free"]):
            bin_row["_free"] = free
            best_partial = bin_row
        return None

    # Pass 1: bins already holding this item
    existing = frappe.get_all(
        "WMS Bin Location",
        filters={"warehouse": warehouse, "current_item": item_code, "status": "Occupied"},
        or_filters=or_filters or None,
        fields=["name", "bin_id", "aisle", "rack", "shelf", "qty_in_bin", "max_capacity"],
    )
    for b in existing:
        free = _free_space(b.name, b.qty_in_bin, b.max_capacity)
        hit = consider(b, free, _("Matching inventory found. Consolidate here."))
        if hit:
            return hit

    # Pass 2: vacant bins (skip any already promised to a different item)
    vacant = frappe.get_all(
        "WMS Bin Location",
        filters={"warehouse": warehouse, "status": "Vacant"},
        or_filters=or_filters or None,
        fields=["name", "bin_id", "aisle", "rack", "shelf", "qty_in_bin", "max_capacity"],
    )
    for b in vacant:
        if frappe.db.exists("WMS Task", {
            "target_bin": b.name, "status": "Open",
            "task_type": "Putaway", "item_code": ["!=", item_code],
        }):
            continue
        free = _free_space(b.name, b.qty_in_bin, b.max_capacity)
        hit = consider(b, free, _("Suggested open bin."))
        if hit:
            return hit

    if best_partial:
        best_partial["message"] = _("Partial space available. Consolidate here.")
        return best_partial

    return {"name": None, "message": _("No available bin with sufficient capacity. Assign manually.")}


@frappe.whitelist()
def confirm_putaway(task_name, scanned_bin_id):
    # --- Lock the task row to prevent double-confirm ---
    locked_task = frappe.db.sql(
        "SELECT name, status, target_bin, item_code, qty "
        "FROM `tabWMS Task` WHERE name = %s FOR UPDATE",
        task_name,
        as_dict=True,
    )
    if not locked_task:
        frappe.throw(_("Task {0} not found.").format(task_name))

    task_state = locked_task[0]
    if task_state.status != "Open":
        frappe.throw(_(
            "This task is already {0}. It may have been confirmed by another worker."
        ).format(task_state.status))

    if not task_state.target_bin:
        frappe.throw(_("This task has no assigned bin yet. Cannot confirm putaway."))

    # --- Lock the bin row to prevent concurrent capacity overflow ---
    locked_bin = frappe.db.sql(
        "SELECT name, bin_id, qty_in_bin, max_capacity, status "
        "FROM `tabWMS Bin Location` WHERE name = %s FOR UPDATE",
        task_state.target_bin,
        as_dict=True,
    )
    if not locked_bin:
        frappe.throw(_("Bin not found."))

    bin_row = locked_bin[0]
    if bin_row.bin_id != scanned_bin_id:
        frappe.throw(_(
            "Scanned bin does not match assigned bin. Expected {0}"
        ).format(bin_row.bin_id))

    qty_in_bin = bin_row.qty_in_bin or 0
    new_qty = qty_in_bin + (task_state.qty or 0)
    if bin_row.max_capacity and new_qty > bin_row.max_capacity:
        frappe.throw(_(
            "Bin {0} capacity exceeded. Max: {1}, Current: {2}, Trying to add: {3}"
        ).format(bin_row.bin_id, bin_row.max_capacity, qty_in_bin, task_state.qty))

    # --- Apply changes ---
    frappe.db.set_value("WMS Bin Location", bin_row.name, {
        "status": "Occupied",
        "current_item": task_state.item_code,
        "qty_in_bin": new_qty,
    })

    frappe.db.set_value("WMS Task", task_name, {
        "status": "Completed",
        "completed_at": frappe.utils.now_datetime(),
    })

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Putaway confirmed at {0}").format(bin_row.bin_id),
    }


@frappe.whitelist()
def retry_bin_suggestion(task_name):
    """
    Re-attempts bin assignment for a task stuck without a target_bin
    (e.g. created before any WMS Bin Location existed for that warehouse).
    """
    settings = get_settings()
    task = frappe.get_doc("WMS Task", task_name)

    if task.target_bin:
        return {"success": False, "message": _("Task already has a target bin assigned.")}

    if task.status != "Open":
        return {"success": False, "message": _("Only Open tasks can be retried.")}

    suggestion = get_suggested_putaway_bin(
        task.item_code, task.warehouse, qty=task.qty,
        allow_partial=settings["allow_partial_bin_fill"],
    )
    if not suggestion.get("name"):
        return {"success": False, "message": _("Still no bin available. Create one first.")}

    task.target_bin = suggestion["name"]
    task.save(ignore_permissions=True)
    frappe.db.commit()

    return {"success": True, "message": _("Bin {0} assigned.").format(suggestion["bin_id"])}


def create_putaway_tasks(doc, method):
    settings = get_settings()
    allow_partial = settings["allow_partial_bin_fill"]

    for item in doc.items:
        remaining_qty = item.qty

        while remaining_qty > 0:
            suggestion = get_suggested_putaway_bin(
                item.item_code,
                item.warehouse,
                qty=remaining_qty,
                allow_partial=allow_partial,
            )

            if not suggestion.get("name"):
                # No bin has room for what's left. Don't block the receipt;
                # create an exception task so a supervisor can resolve it.
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
                    "exception_reason": "Bin Full",  # consider a more specific reason, e.g. "No Eligible Bin"
                    "exception_notes": _(
                        "No vacant or matching bin with enough space in warehouse {0}."
                    ).format(item.warehouse),
                    "exception_reported_by": frappe.session.user,
                    "exception_reported_at": frappe.utils.now_datetime(),
                }).insert(ignore_permissions=True)
                break

            # Free space already accounts for qty_in_bin AND all Open tasks
            # targeting this bin (including ones inserted earlier in this loop).
            free = _free_space(
                suggestion["name"],
                suggestion.get("qty_in_bin"),
                suggestion.get("max_capacity"),
            )
            qty_for_this_bin = remaining_qty if free is None else min(remaining_qty, free)

            # Safety net: avoid an infinite loop or a zero-qty task
            if qty_for_this_bin <= 0:
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
                    "exception_notes": _("Suggested bin {0} has no free space.").format(
                        suggestion["name"]
                    ),
                    "exception_reported_by": frappe.session.user,
                    "exception_reported_at": frappe.utils.now_datetime(),
                }).insert(ignore_permissions=True)
                break

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

            remaining_qty -= qty_for_this_bin


@frappe.whitelist()
def report_exception(task_name, exception_reason, exception_notes=None):
    locked = frappe.db.sql(
        "SELECT name, status, target_bin FROM `tabWMS Task` "
        "WHERE name = %s FOR UPDATE",
        task_name,
        as_dict=True,
    )
    if not locked:
        frappe.throw(_("Task {0} not found.").format(task_name))

    row = locked[0]
    if row.status == "Completed":
        frappe.throw(_("This task is already completed."))
    if row.status == "Exception":
        frappe.throw(_("This task is already flagged as an exception."))

    frappe.db.set_value("WMS Task", task_name, {
        "status": "Exception",
        "exception_reason": exception_reason,
        "exception_notes": exception_notes,
        "exception_reported_by": frappe.session.user,
        "exception_reported_at": frappe.utils.now_datetime(),
    })

    if exception_reason in ("Bin Full", "Bin Damaged or Missing") and row.target_bin:
        frappe.db.set_value("WMS Bin Location", row.target_bin, "status", "Blocked")

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Exception reported. A supervisor will review this task."),
    }


@frappe.whitelist()
def resolve_exception(task_name, reassign_new_bin=True):
    require_supervisor()
    task = frappe.get_doc("WMS Task", task_name)

    if task.status != "Exception":
        frappe.throw(_("Only tasks with status 'Exception' can be resolved this way."))

    task_type = task.task_type

    # --- Pick task resolution ---
    if task_type == "Pick":
        if reassign_new_bin:
            return _reassign_pick(task)

        # Just reopen for manual handling — no new bin assignment
        task.status = "Open"
        task.exception_reason = None
        task.exception_notes = None
        task.exception_reported_by = None
        task.exception_reported_at = None
        task.save(ignore_permissions=True)

        # Re-reserve on the same bin
        if task.source_bin and task.qty:
            bin_doc = frappe.get_doc("WMS Bin Location", task.source_bin)
            bin_doc.qty_reserved = (bin_doc.qty_reserved or 0) + task.qty
            bin_doc.save(ignore_permissions=True)

        frappe.db.commit()
        return {"success": True, "message": _("Pick task reopened on same bin.")}

    # --- Putaway task resolution (existing behaviour) ---
    task.target_bin = None
    task.status = "Open"
    task.exception_reason = None
    task.exception_notes = None
    task.exception_reported_by = None
    task.exception_reported_at = None
    task.save(ignore_permissions=True)

    if reassign_new_bin:
        result = retry_bin_suggestion(task.name)
        return result

    frappe.db.commit()
    return {"success": True, "message": _("Task reopened for manual bin assignment.")}


def _reassign_pick(task):
    """
    For a pick exception: clear the source_bin, then allocate a new bin
    from scratch using the same FIFO rules. Excludes the bin we just
    reported as problematic.
    """
    from wms.api.picking import _get_bins_for_item

    # Note the bin we're moving away from
    old_bin = task.source_bin

    bins = _get_bins_for_item(task.item_code, task.warehouse)
    # Skip the old bin (the one reported problematic)
    bins = [b for b in bins if b["name"] != old_bin]

    if not bins:
        return {
            "success": False,
            "message": _(
                "No alternative bin found for {0} in {1}. "
                "Investigate the reported bin first."
            ).format(task.item_code, task.warehouse),
        }

    # Take the first (FIFO order) bin with enough space
    required = task.qty or 0
    chosen = None
    for b in bins:
        if b["available"] >= required:
            chosen = b
            break

    if not chosen:
        # Try to at least allocate partial
        bins_with_space = [b for b in bins if b["available"] > 0]
        if not bins_with_space:
            return {
                "success": False,
                "message": _("No bin has stock of {0}.").format(task.item_code),
            }
        # Use the one with the most available
        chosen = max(bins_with_space, key=lambda x: x["available"])
        if chosen["available"] < required:
            return {
                "success": False,
                "message": _(
                    "Only {0} unit(s) available across bins; {1} required. "
                    "Consider cancelling the pick."
                ).format(chosen["available"], required),
            }

    # Reserve on the new bin, mark task Open again
    frappe.db.set_value("WMS Bin Location", chosen["name"], {
        "qty_reserved": (chosen["qty_reserved"] or 0) + required,
    }, update_modified=False)

    frappe.db.set_value("WMS Task", task.name, {
        "status": "Open",
        "source_bin": chosen["name"],
        "exception_reason": None,
        "exception_notes": None,
        "exception_reported_by": None,
        "exception_reported_at": None,
    }, update_modified=False)

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Pick reassigned to bin {0}.").format(chosen["bin_id"]),
    }


@frappe.whitelist()
def get_exception_tasks(warehouse=None):
    require_supervisor()
    filters = {"status": "Exception"}
    if warehouse:
        filters["warehouse"] = warehouse
    return frappe.get_all("WMS Task", filters=filters,
        fields=["name", "task_type", "item_code", "qty", "target_bin", "source_bin", "warehouse","delivery_note", "customer", 
                "exception_reason", "exception_notes", "exception_reported_by", "exception_reported_at"])


def require_supervisor():
    role = get_settings()["wms_supervisor_role"]
    if role not in frappe.get_roles(frappe.session.user):
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


def _task_links(task_names):
    """Return comma-separated clickable links for WMS Task names."""
    return ", ".join(
        '<a href="{0}" target="_blank">{1}</a>'.format(
            get_url_to_form("WMS Task", name), frappe.bold(name)
        )
        for name in task_names
    )


def cancel_putaway_tasks(doc, method):
    """
    Runs before a Purchase Receipt is cancelled.

    - Open/Exception tasks are cancelled automatically (they never moved stock).
    - If any Completed tasks exist, cancellation is BLOCKED — a supervisor must
      reverse them in the WMS app first.
    """
    linked_tasks = frappe.get_all(
        "WMS Task",
        filters={
            "reference_doctype": "Purchase Receipt",
            "reference_name": doc.name,
            "status": ["in", ["Open", "Exception", "Completed"]],
        },
        fields=["name", "status"],
    )

    if not linked_tasks:
        return

    completed = [t for t in linked_tasks if t.status == "Completed"]
    open_exc = [t for t in linked_tasks if t.status in ("Open", "Exception")]

    if completed:
        names = ", ".join(t.name for t in completed)
        frappe.throw(_(
            "Cannot cancel this Purchase Receipt: {0} putaway task(s) are already "
            "Completed. A supervisor must reverse them in the WMS app first. "
            "Completed tasks: {1}"
        ).format(len(completed), names))

    # Safe to cancel Open / Exception tasks
    for t in open_exc:
        frappe.db.set_value("WMS Task", t.name, "status", "Cancelled")

    if open_exc:
        frappe.db.commit()
        frappe.msgprint(
            _("Cancelled {0} pending WMS task(s).").format(len(open_exc)),
            indicator="orange",
        )


@frappe.whitelist()
def get_bin_details(bin_name):
    """
    Returns full details for a WMS Bin Location including its recent
    putaway movements. Used by the BinDetail page.
    """
    bin_doc = frappe.db.get_value(
        "WMS Bin Location",
        bin_name,
        ["name", "bin_id", "warehouse", "bin_type", "status",
         "current_item", "qty_in_bin", "max_capacity", "aisle", "rack", "shelf"],
        as_dict=True,
    )
    if not bin_doc:
        frappe.throw(_("Bin {0} not found.").format(bin_name))

    qty_in_bin = bin_doc.qty_in_bin or 0
    max_capacity = bin_doc.max_capacity or 0
    remaining = (max_capacity - qty_in_bin) if max_capacity else None

    # Recent completed movements into this bin (putaway only for now)
    movements = frappe.get_all(
        "WMS Task",
        filters={"target_bin": bin_name, "status": "Completed"},
        fields=["name", "item_code", "qty", "completed_at", "modified_by"],
        order_by="completed_at desc",
        limit=20,
    )

    return {
        "name": bin_doc.name,
        "bin_id": bin_doc.bin_id,
        "warehouse": bin_doc.warehouse,
        "bin_type": bin_doc.bin_type,
        "status": bin_doc.status,
        "current_item": bin_doc.current_item,
        "qty_in_bin": qty_in_bin,
        "max_capacity": max_capacity,
        "remaining": remaining,
        "aisle": bin_doc.aisle,
        "rack": bin_doc.rack,
        "shelf": bin_doc.shelf,
        "movements": movements,
    }

@frappe.whitelist()
def unblock_bin(bin_name):
    """
    Supervisor action: clears the Blocked status from a bin.
    Auto-decides Vacant vs Occupied based on current qty.
    """
    require_supervisor()

    bin_doc = frappe.get_doc("WMS Bin Location", bin_name)
    if bin_doc.status != "Blocked":
        return {"success": False, "message": _("Bin is not blocked.")}

    bin_doc.status = "Occupied" if (bin_doc.qty_in_bin or 0) > 0 else "Vacant"
    bin_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "new_status": bin_doc.status,
        "message": _("Bin {0} unblocked (now {1}).").format(bin_doc.bin_id, bin_doc.status),
    }


@frappe.whitelist()
def get_bins(search=None, status=None, warehouse=None, limit=100):
    """
    List WMS Bin Locations with optional filters.
      search    matches bin_id OR current_item (substring)
      status    Vacant / Occupied / Blocked
      warehouse filter by warehouse
    """
    filters = {}
    if status:
        filters["status"] = status
    if warehouse:
        filters["warehouse"] = warehouse

    or_filters = None
    if search:
        or_filters = [
            ["bin_id", "like", f"%{search}%"],
            ["current_item", "like", f"%{search}%"],
        ]

    rows = frappe.get_all(
        "WMS Bin Location",
        filters=filters or None,
        or_filters=or_filters,
        fields=[
            "name", "bin_id", "warehouse", "bin_type", "status",
            "current_item", "qty_in_bin", "max_capacity",
            "aisle", "rack", "shelf",
        ],
        order_by="bin_id asc",
        limit_page_length=int(limit),
    )
    return rows


@frappe.whitelist()
def get_completed_putaways(limit=50):
    """
    Supervisor-only: recent completed putaway tasks eligible for reversal.
    """
    require_supervisor()
    return frappe.get_all(
        "WMS Task",
        filters={"task_type": "Putaway", "status": "Completed"},
        fields=["name", "item_code", "qty", "target_bin", "warehouse",
                "completed_at", "reference_name"],
        order_by="completed_at desc",
        limit_page_length=int(limit),
    )


@frappe.whitelist()
def reverse_putaway(task_name, reason, notes=None):
    """
    Supervisor-only. Reverses a completed putaway:
      - Decrements the target bin's qty_in_bin by task.qty
      - Marks the task Reversed (never deleted)
      - Records who, when, why

    Refuses if the bin doesn't hold enough stock (the goods may have already
    been picked or moved).
    """
    require_supervisor()

    if not reason:
        frappe.throw(_("Reversal reason is required."))

    # Lock the task row
    locked_task = frappe.db.sql(
        "SELECT name, status, target_bin, item_code, qty "
        "FROM `tabWMS Task` WHERE name = %s FOR UPDATE",
        task_name,
        as_dict=True,
    )
    if not locked_task:
        frappe.throw(_("Task {0} not found.").format(task_name))

    task = locked_task[0]
    if task.status != "Completed":
        frappe.throw(_(
            "Only Completed tasks can be reversed. This task is {0}."
        ).format(task.status))

    if not task.target_bin:
        frappe.throw(_("This task has no target bin — cannot reverse."))

    # Lock the bin row
    locked_bin = frappe.db.sql(
        "SELECT name, bin_id, qty_in_bin FROM `tabWMS Bin Location` "
        "WHERE name = %s FOR UPDATE",
        task.target_bin,
        as_dict=True,
    )
    if not locked_bin:
        frappe.throw(_("Bin not found."))

    bin_row = locked_bin[0]
    current_qty = bin_row.qty_in_bin or 0
    reverse_qty = task.qty or 0

    if reverse_qty > current_qty:
        frappe.throw(_(
            "Cannot reverse {0} unit(s) — bin {1} only has {2} in it. "
            "The stock may have already been picked or moved."
        ).format(reverse_qty, bin_row.bin_id, current_qty))

    new_qty = current_qty - reverse_qty

    # Update bin
    bin_update = {"qty_in_bin": new_qty}
    if new_qty == 0:
        bin_update["status"] = "Vacant"
        bin_update["current_item"] = None

    frappe.db.set_value("WMS Bin Location", bin_row.name, bin_update)

    # Update task
    frappe.db.set_value("WMS Task", task_name, {
        "status": "Reversed",
        "reversed_at": frappe.utils.now_datetime(),
        "reversed_by": frappe.session.user,
        "reversal_reason": reason,
        "reversal_notes": notes or "",
    })

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Putaway reversed. {0} unit(s) removed from {1}.").format(
            reverse_qty, bin_row.bin_id
        ),
        "new_bin_qty": new_qty,
    }