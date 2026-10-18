import frappe
from frappe import _
from wms.wms.doctype.wms_settings.wms_settings import get_settings
from wms.api.putaway import require_supervisor


@frappe.whitelist()
def get_draft_delivery_notes(search=None):
    """
    Returns Draft Delivery Notes filtered by user's Company permissions.
    Optional `search` matches DN name or customer.
    """
    user_companies = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Company"},
        pluck="for_value",
    )

    conditions = ["dn.docstatus = 0"]
    params = {}

    if user_companies:
        conditions.append("dn.company IN %(companies)s")
        params["companies"] = tuple(user_companies)

    if search:
        conditions.append(
            "(dn.name LIKE %(search)s OR dn.customer LIKE %(search)s "
            "OR dn.customer_name LIKE %(search)s)"
        )
        params["search"] = f"%{search}%"

    where = " AND ".join(conditions)

    rows = frappe.db.sql(f"""
        SELECT
            dn.name,
            dn.customer,
            dn.customer_name,
            dn.company,
            dn.posting_date,
            dn.status,
            (SELECT COUNT(*) FROM `tabDelivery Note Item` dni
             WHERE dni.parent = dn.name) AS line_count,
            (SELECT COUNT(*) FROM `tabWMS Task` wt
             WHERE wt.delivery_note = dn.name AND wt.task_type = 'Pick') AS pick_tasks
        FROM `tabDelivery Note` dn
        WHERE {where}
        ORDER BY dn.posting_date DESC, dn.name DESC
        LIMIT 50
    """, params, as_dict=True)

    return rows


@frappe.whitelist()
def get_delivery_note_details(dn_name):
    """
    Returns DN header + lines with bin availability.
    Used by the mobile "Generate Pick Tasks" preview screen.
    """
    dn = frappe.get_doc("Delivery Note", dn_name)

    if dn.docstatus != 0:
        frappe.throw(_("Only Draft Delivery Notes can have pick tasks generated."))

    already_generated = bool(frappe.db.exists(
        "WMS Task", {"task_type": "Pick", "delivery_note": dn.name}
    ))

    lines = []
    for item in dn.items:
        bins = _get_bins_for_item(item.item_code, item.warehouse)
        lines.append({
            "dn_detail": item.name,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": item.qty,
            "uom": item.uom,
            "warehouse": item.warehouse,
            "available_bins": len(bins),
            "total_available": sum(b["available"] for b in bins),
        })

    return {
        "name": dn.name,
        "customer": dn.customer,
        "customer_name": dn.customer_name,
        "company": dn.company,
        "posting_date": str(dn.posting_date),
        "lines": lines,
        "already_generated": already_generated,
    }


def _get_bins_for_item(item_code, warehouse):
    """
    Find bins in this warehouse holding this item, sorted FIFO
    (creation asc, then name asc for deterministic tie-break).
    """
    bins = frappe.get_all(
        "WMS Bin Location",
        filters={
            "warehouse": warehouse,
            "current_item": item_code,
            "status": ["in", ["Occupied", "Reserved"]],
        },
        fields=["name", "bin_id", "qty_in_bin", "qty_reserved", "max_capacity", "creation"],
        order_by="creation asc, name asc",
    )

    result = []
    for b in bins:
        available = (b.qty_in_bin or 0) - (b.qty_reserved or 0)
        if available <= 0:
            continue
        b["available"] = available
        result.append(b)

    return result


@frappe.whitelist()
def generate_pick_tasks(dn_name, called_from_hook=False):
    """
    Idempotent. Allocates bins FIFO. Reserves qty_reserved on each source bin.
    Creates one Pick task per (item, bin) split.
    Creates an Exception task for any shortfall.

    `called_from_hook=True` bypasses the supervisor role check, since hooks
    fire as the system (or as the user who triggered the DN creation).
    """
    if not called_from_hook:
        require_supervisor()

    dn = frappe.get_doc("Delivery Note", dn_name)
    if dn.docstatus != 0:
        frappe.throw(_("Only Draft Delivery Notes can have pick tasks generated."))

    if frappe.db.exists("WMS Task", {
        "task_type": "Pick",
        "delivery_note": dn.name,
        "status": ["in", ["Open", "Exception"]],
    }):
        frappe.throw(_(
            "Open or exception pick tasks already exist for this Delivery Note. "
            "Cancel them first before regenerating."
        ))

    tasks_created = 0
    shortfalls = 0

    for item in dn.items:
        required = frappe.utils.flt(item.qty)
        if required <= 0:
            continue

        bins = _get_bins_for_item(item.item_code, item.warehouse)
        remaining = required

        for b in bins:
            if remaining <= 0:
                break

            allocate = min(remaining, b["available"])
            if allocate <= 0:
                continue

            frappe.get_doc({
                "doctype": "WMS Task",
                "company": dn.company,
                "task_type": "Pick",
                "reference_doctype": "Delivery Note",
                "reference_name": dn.name,
                "delivery_note": dn.name,
                "sales_order": item.against_sales_order,
                "customer": dn.customer,
                "item_code": item.item_code,
                "qty": allocate,
                "source_bin": b["name"],
                "warehouse": item.warehouse,
                "status": "Open",
            }).insert(ignore_permissions=True)
            tasks_created += 1

            new_reserved = (b["qty_reserved"] or 0) + allocate
            frappe.db.set_value(
                "WMS Bin Location", b["name"],
                "qty_reserved", new_reserved,
                update_modified=False,
            )

            remaining -= allocate

        if remaining > 0:
            frappe.get_doc({
                "doctype": "WMS Task",
                "company": dn.company,
                "task_type": "Pick",
                "reference_doctype": "Delivery Note",
                "reference_name": dn.name,
                "delivery_note": dn.name,
                "customer": dn.customer,
                "item_code": item.item_code,
                "qty": remaining,
                "warehouse": item.warehouse,
                "status": "Exception",
                "exception_reason": "Other",
                "exception_notes": _(
                    "Insufficient bin stock: {0} unit(s) short in warehouse {1}."
                ).format(remaining, item.warehouse),
                "exception_reported_by": frappe.session.user,
                "exception_reported_at": frappe.utils.now_datetime(),
            }).insert(ignore_permissions=True)
            shortfalls += 1

    frappe.db.commit()

    return {
        "success": True,
        "tasks_created": tasks_created,
        "shortfalls": shortfalls,
        "message": _("Generated {0} pick task(s). {1} shortfall line(s).").format(
            tasks_created, shortfalls
        ),
    }


@frappe.whitelist()
def get_pick_tasks(warehouse=None):
    """
    Open pick tasks for the mobile worker.
    """
    filters = {"task_type": "Pick", "status": "Open"}
    if warehouse:
        filters["warehouse"] = warehouse

    return frappe.get_all(
        "WMS Task",
        filters=filters,
        fields=[
            "name", "item_code", "qty", "source_bin", "warehouse",
            "delivery_note", "customer",
        ],
        order_by="creation asc",
    )


@frappe.whitelist()
def get_pick_task_details(task_name):
    """
    Task + source bin info + item barcode target + settings.
    """
    task = frappe.get_doc("WMS Task", task_name)
    if task.task_type != "Pick":
        frappe.throw(_("Task {0} is not a pick task.").format(task_name))

    settings = get_settings()

    bin_info = None
    if task.source_bin:
        bin_row = frappe.db.get_value(
            "WMS Bin Location", task.source_bin,
            ["bin_id", "qty_in_bin", "qty_reserved", "max_capacity"],
            as_dict=True,
        )
        if bin_row:
            bin_info = {
                "name": task.source_bin,
                "bin_id": bin_row.bin_id,
                "qty_in_bin": bin_row.qty_in_bin or 0,
                "qty_reserved": bin_row.qty_reserved or 0,
                "available": (bin_row.qty_in_bin or 0) - (bin_row.qty_reserved or 0),
            }

    return {
        "name": task.name,
        "item_code": task.item_code,
        "qty": task.qty,
        "source_bin": task.source_bin,
        "bin_info": bin_info,
        "delivery_note": task.delivery_note,
        "customer": task.customer,
        "warehouse": task.warehouse,
        "require_item_scan_on_pick": settings["require_item_scan_on_pick"],
    }


@frappe.whitelist()
def confirm_pick(task_name, scanned_bin_id, picked_qty, scanned_item_code=None):
    """
    Confirm a pick:
      - Lock task and bin rows
      - Validate scanned bin matches source_bin
      - Validate item code if required
      - Decrement bin qty_in_bin by picked_qty
      - Release the full reservation (task.qty)
      - Mark task Completed with picked_qty
      - If picked_qty < task.qty, create a Short Pick exception
    """
    settings = get_settings()
    picked_qty = frappe.utils.flt(picked_qty)

    if picked_qty <= 0:
        frappe.throw(_("Picked qty must be greater than zero. Use Report Issue for zero picks."))

    locked_task = frappe.db.sql(
        "SELECT name, status, source_bin, item_code, qty, delivery_note, customer, "
        "warehouse, company FROM `tabWMS Task` WHERE name = %s FOR UPDATE",
        task_name, as_dict=True,
    )
    if not locked_task:
        frappe.throw(_("Task {0} not found.").format(task_name))

    task = locked_task[0]
    if task.status != "Open":
        frappe.throw(_(
            "This task is already {0}. It may have been confirmed by another worker."
        ).format(task.status))

    if not task.source_bin:
        frappe.throw(_("This task has no source bin assigned."))

    if picked_qty > (task.qty or 0):
        frappe.throw(_(
            "Picked qty ({0}) cannot exceed requested qty ({1})."
        ).format(picked_qty, task.qty))

    if settings["require_item_scan_on_pick"]:
        if not scanned_item_code:
            frappe.throw(_("Item scan is required. Please scan the item barcode."))
        if scanned_item_code != task.item_code:
            frappe.throw(_(
                "Scanned item {0} does not match expected {1}."
            ).format(scanned_item_code, task.item_code))

    locked_bin = frappe.db.sql(
        "SELECT name, bin_id, qty_in_bin, qty_reserved "
        "FROM `tabWMS Bin Location` WHERE name = %s FOR UPDATE",
        task.source_bin, as_dict=True,
    )
    if not locked_bin:
        frappe.throw(_("Source bin not found."))

    bin_row = locked_bin[0]
    if bin_row.bin_id != scanned_bin_id:
        frappe.throw(_(
            "Scanned bin does not match source bin. Expected {0}"
        ).format(bin_row.bin_id))

    current_qty = bin_row.qty_in_bin or 0
    current_reserved = bin_row.qty_reserved or 0
    reserve_release = task.qty or 0

    if picked_qty > current_qty:
        frappe.throw(_(
            "Bin {0} only has {1} unit(s), cannot pick {2}."
        ).format(bin_row.bin_id, current_qty, picked_qty))

    new_qty = current_qty - picked_qty
    new_reserved = max(0, current_reserved - reserve_release)

    bin_update = {"qty_in_bin": new_qty, "qty_reserved": new_reserved}
    if new_qty == 0:
        bin_update["status"] = "Vacant"
        bin_update["current_item"] = None

    frappe.db.set_value("WMS Bin Location", bin_row.name, bin_update, update_modified=False)

    frappe.db.set_value("WMS Task", task_name, {
        "status": "Completed",
        "picked_qty": picked_qty,
        "completed_at": frappe.utils.now_datetime(),
    }, update_modified=False)

    short_qty = (task.qty or 0) - picked_qty
    if short_qty > 0:
        frappe.get_doc({
            "doctype": "WMS Task",
            "company": task.company,
            "task_type": "Pick",
            "reference_doctype": "Delivery Note",
            "reference_name": task.delivery_note,
            "delivery_note": task.delivery_note,
            "customer": task.customer,
            "item_code": task.item_code,
            "qty": short_qty,
            "warehouse": task.warehouse,
            "status": "Exception",
            "exception_reason": "Other",
            "exception_notes": _(
                "Short pick: {0} unit(s) of {1} could not be picked from {2}."
            ).format(short_qty, task.item_code, bin_row.bin_id),
            "exception_reported_by": frappe.session.user,
            "exception_reported_at": frappe.utils.now_datetime(),
        }).insert(ignore_permissions=True)

    frappe.db.commit()

    msg = _("Picked {0} unit(s) from {1}.").format(picked_qty, bin_row.bin_id)
    if short_qty > 0:
        msg += " " + _("{0} unit(s) short — flagged for supervisor.").format(short_qty)

    return {
        "success": True,
        "picked_qty": picked_qty,
        "short_qty": short_qty,
        "new_bin_qty": new_qty,
        "new_bin_reserved": new_reserved,
        "message": msg,
    }


@frappe.whitelist()
def cancel_pick_task(task_name, reason=None):
    """
    Supervisor-only: cancels an Open or Exception pick task and releases
    its reservation (if any).
    """
    require_supervisor()

    locked_task = frappe.db.sql(
        "SELECT name, status, source_bin, qty FROM `tabWMS Task` WHERE name = %s FOR UPDATE",
        task_name, as_dict=True,
    )
    if not locked_task:
        frappe.throw(_("Task {0} not found.").format(task_name))

    task = locked_task[0]
    if task.status not in ("Open", "Exception"):
        frappe.throw(_("Only Open or Exception pick tasks can be cancelled."))

    if task.source_bin and task.status == "Open":
        locked_bin = frappe.db.sql(
            "SELECT name, qty_reserved FROM `tabWMS Bin Location` WHERE name = %s FOR UPDATE",
            task.source_bin, as_dict=True,
        )
        if locked_bin:
            current_reserved = locked_bin[0].qty_reserved or 0
            new_reserved = max(0, current_reserved - (task.qty or 0))
            frappe.db.set_value(
                "WMS Bin Location", task.source_bin,
                "qty_reserved", new_reserved,
                update_modified=False,
            )

    frappe.db.set_value("WMS Task", task_name, {
        "status": "Cancelled",
        "exception_notes": reason or "",
    }, update_modified=False)

    frappe.db.commit()

    return {"success": True, "message": _("Pick task cancelled and reservation released.")}


@frappe.whitelist()
def report_pick_exception(task_name, reason, notes=None):
    """
    Called from the mobile app when a picker can't complete the task.
    Releases any reservation and marks the task as an Exception for
    supervisor review. Does NOT decrement bin stock.

    Reasons: 'Bin Empty', 'Wrong Item', 'Item Damaged', 'Other'
    """
    valid_reasons = {"Bin Empty", "Wrong Item", "Item Damaged", "Other"}
    if reason not in valid_reasons:
        frappe.throw(_("Invalid pick exception reason: {0}").format(reason))

    locked_task = frappe.db.sql(
        "SELECT name, status, source_bin, qty, item_code, delivery_note, customer, company "
        "FROM `tabWMS Task` WHERE name = %s FOR UPDATE",
        task_name, as_dict=True,
    )
    if not locked_task:
        frappe.throw(_("Task {0} not found.").format(task_name))

    task = locked_task[0]
    if task.status != "Open":
        frappe.throw(_(
            "Only Open pick tasks can be reported. This task is {0}."
        ).format(task.status))

    # Release the reservation so the qty is available for reassignment
    if task.source_bin:
        locked_bin = frappe.db.sql(
            "SELECT name, qty_reserved FROM `tabWMS Bin Location` WHERE name = %s FOR UPDATE",
            task.source_bin, as_dict=True,
        )
        if locked_bin:
            current_reserved = locked_bin[0].qty_reserved or 0
            new_reserved = max(0, current_reserved - (task.qty or 0))
            frappe.db.set_value(
                "WMS Bin Location", task.source_bin,
                "qty_reserved", new_reserved,
                update_modified=False,
            )

    frappe.db.set_value("WMS Task", task_name, {
        "status": "Exception",
        "exception_reason": reason,
        "exception_notes": notes or "",
        "exception_reported_by": frappe.session.user,
        "exception_reported_at": frappe.utils.now_datetime(),
    }, update_modified=False)

    # If bin physically lacks the stock it claims, mark it blocked
    if reason == "Bin Empty" and task.source_bin:
        frappe.db.set_value("WMS Bin Location", task.source_bin, "status", "Blocked")

    frappe.db.commit()

    return {
        "success": True,
        "message": _("Issue reported. A supervisor will review this pick."),
    }


# ---------------------------------------------------------------------------
# Delivery Note hooks
# ---------------------------------------------------------------------------

def auto_release_pick_tasks_on_create(doc, method):
    """
    Fires after a Delivery Note is created. If WMS Settings has
    Auto-Release enabled and the DN is a Draft, generate pick tasks.
    Errors are logged but do not block DN creation.
    """
    settings = get_settings()
    if settings.get("pick_release_mode") != "Auto-Release on DN Creation":
        return

    if doc.docstatus != 0:
        return  # only drafts

    try:
        result = generate_pick_tasks(doc.name, called_from_hook=True)
        if result.get("shortfalls"):
            frappe.msgprint(
                _("Auto-release: {0} shortfall line(s) flagged for supervisor review.").format(
                    result["shortfalls"]
                ),
                indicator="orange",
                alert=True,
            )
    except Exception as e:
        frappe.log_error(
            f"Auto-release of pick tasks failed for DN {doc.name}: {e}",
            "WMS Auto Release",
        )


def validate_dn_submit(doc, method):
    """
    Blocks DN submit if any pick tasks for this DN are still Open or Exception.
    """
    incomplete = frappe.db.count("WMS Task", {
        "task_type": "Pick",
        "delivery_note": doc.name,
        "status": ["in", ["Open", "Exception"]],
    })
    if incomplete:
        frappe.throw(_(
            "Cannot submit this Delivery Note: {0} pick task(s) are still "
            "Open or in Exception. Complete or cancel them first."
        ).format(incomplete))


def release_dn_pick_reservations(doc, method):
    """
    Fires on DN trash or cancel. Cancels all Open/Exception pick tasks for
    this DN and releases their reservations so bin stock becomes available.
    """
    tasks = frappe.get_all(
        "WMS Task",
        filters={
            "task_type": "Pick",
            "delivery_note": doc.name,
            "status": ["in", ["Open", "Exception"]],
        },
        fields=["name", "source_bin", "qty", "status"],
    )

    for t in tasks:
        # Release reservation on Open tasks only (Exceptions already released)
        if t.status == "Open" and t.source_bin:
            bin_row = frappe.db.get_value(
                "WMS Bin Location", t.source_bin,
                ["qty_reserved"], as_dict=True,
            )
            if bin_row:
                new_reserved = max(0, (bin_row.qty_reserved or 0) - (t.qty or 0))
                frappe.db.set_value(
                    "WMS Bin Location", t.source_bin,
                    "qty_reserved", new_reserved,
                    update_modified=False,
                )

        frappe.db.set_value(
            "WMS Task", t.name, "status", "Cancelled",
            update_modified=False,
        )

    if tasks:
        frappe.db.commit()