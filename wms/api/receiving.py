import frappe
from frappe import _
from wms.wms.doctype.wms_settings.wms_settings import get_settings


@frappe.whitelist()
def get_open_purchase_orders(search=None):
    """
    Returns POs with at least one line having pending qty > 0,
    filtered by the user's Company permissions.
    Optional `search` matches PO name, supplier name, or supplier ID.
    """
    user_companies = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Company"},
        pluck="for_value",
    )

    params = {}
    company_clause = ""
    if user_companies:
        company_clause = "AND po.company IN %(companies)s"
        params["companies"] = tuple(user_companies)

    search_clause = ""
    if search:
        search_clause = """
            AND (
                po.name LIKE %(search)s
                OR po.supplier LIKE %(search)s
                OR po.supplier_name LIKE %(search)s
            )
        """
        params["search"] = f"%{search}%"

    rows = frappe.db.sql(
        f"""
        SELECT DISTINCT
            po.name,
            po.supplier,
            po.supplier_name,
            po.company,
            po.transaction_date,
            po.status
        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
        WHERE po.docstatus = 1
          AND po.status NOT IN ('Closed', 'Completed')
          AND (poi.qty - poi.received_qty) > 0
          {company_clause}
          {search_clause}
        ORDER BY po.transaction_date DESC, po.name DESC
        LIMIT 50
        """,
        params,
        as_dict=True,
    )
    return rows


@frappe.whitelist()
def get_purchase_order_details(po_name):
    """
    Returns a PO's header + lines with ordered / received / pending qty,
    plus the warehouse defaults the receiving form will prefill.
    """
    po = frappe.get_doc("Purchase Order", po_name)

    settings = get_settings()

    lines = []
    for row in po.items:
        pending = (row.qty or 0) - (row.received_qty or 0)
        if pending <= 0:
            continue

        lines.append({
            "po_detail": row.name,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "uom": row.uom,
            "ordered_qty": row.qty,
            "received_qty": row.received_qty or 0,
            "pending_qty": pending,
            "rate": row.rate,
            "default_warehouse": row.warehouse or po.set_warehouse or None,
            "needs_qc": _item_needs_qc(row.item_code),
            "existing_short_reason": row.get("wms_short_reason") or "",
            "existing_short_notes": row.get("wms_short_notes") or "",
        })

    return {
        "name": po.name,
        "supplier": po.supplier,
        "supplier_name": po.supplier_name,
        "company": po.company,
        "transaction_date": str(po.transaction_date),
        "lines": lines,
        "settings": {
            "receiving_mode": settings["receiving_mode"],
            "enable_qc_hold_gate": settings["enable_qc_hold_gate"],
            "default_quarantine_warehouse": settings["default_quarantine_warehouse"],
            "default_rejected_warehouse": settings["default_rejected_warehouse"],
            "capture_short_receipt_reason": settings["capture_short_receipt_reason"],
        },
    }


@frappe.whitelist()
def get_receiving_config():
    """
    Returns the settings the receiving screens need to render themselves
    and route qty correctly.
    """
    settings = get_settings()
    return {
        "receiving_mode": settings["receiving_mode"],
        "enable_qc_hold_gate": settings["enable_qc_hold_gate"],
        "default_quarantine_warehouse": settings["default_quarantine_warehouse"],
        "default_rejected_warehouse": settings["default_rejected_warehouse"],
        "capture_short_receipt_reason": settings["capture_short_receipt_reason"],
    }


def _item_needs_qc(item_code):
    """
    True if the item master requires inspection before purchase.
    ERPNext has a field `inspection_required_before_purchase` on Item.
    Falls back to False if the field isn't present on this ERPNext version.
    """
    meta = frappe.get_meta("Item")
    if not meta.has_field("inspection_required_before_purchase"):
        return False
    return bool(frappe.db.get_value("Item", item_code, "inspection_required_before_purchase"))


@frappe.whitelist()
def create_purchase_receipt(payload):
    """
    Creates and submits a Purchase Receipt from the dock worker's input.

    payload = {
        "po_name": "PUR-ORD-2026-00001",
        "lines": [
            {
                "po_detail": "37rd45219o",       # PO Item row name
                "received_qty": 1,               # total physically arrived (incl. damaged)
                "damaged_qty": 0,                # subset of received_qty that's damaged
                "warehouse": "Stores - GSPL",    # optional override
                "short_reason": "Supplier Short Shipped",  # required if short & setting ON
                "short_notes": "free text"       # optional
            }
        ]
    }

    Routing rules applied per line:
      - accepted qty = received_qty - damaged_qty  → main warehouse (or quarantine if QC required)
      - damaged qty                                → default_rejected_warehouse
      - short qty   = pending_qty - received_qty   → stays as pending on the PO
                                                     (reason captured if setting ON)

    The existing on_submit hook fires create_putaway_tasks for accepted qty only.
    """
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)

    settings = get_settings()
    capture_short = settings["capture_short_receipt_reason"]

    po = frappe.get_doc("Purchase Order", payload["po_name"])
    if po.docstatus != 1:
        frappe.throw(_("Purchase Order must be submitted before receiving."))

    # Defensive: confirm the fields we write to actually exist on the target
    # doctype. Frappe silently drops unknown fieldnames in append(), which
    # previously caused the received_qty to never update on the PO.
    _required_pr_fields = {"purchase_order", "purchase_order_item"}
    _pr_fieldnames = {f.fieldname for f in frappe.get_meta("Purchase Receipt Item").fields}
    _missing = _required_pr_fields - _pr_fieldnames
    if _missing:
        frappe.throw(_(
            "Internal error: Purchase Receipt Item is missing required "
            "field(s): {0}. Contact support."
        ).format(", ".join(_missing)))

    # Lock all PO Item rows for this PO for the duration of the transaction.
    # Prevents two concurrent receiving calls from both seeing pending_qty > 0
    # and creating duplicate PRs (over-receipt race condition).
    frappe.db.sql("""
        SELECT name FROM `tabPurchase Order Item`
        WHERE parent = %s FOR UPDATE
    """, po.name)

    pr = frappe.new_doc("Purchase Receipt")
    pr.supplier = po.supplier
    pr.company = po.company
    pr.posting_date = frappe.utils.today()

    po_items_by_rowname = {row.name: row for row in po.items}
    any_line_added = False
    shorts_to_record = []  # collected for post-submit writeback

    for input_line in payload.get("lines", []):
        received = frappe.utils.flt(input_line.get("received_qty"))
        if received <= 0:
            continue

        po_row = po_items_by_rowname.get(input_line.get("po_detail"))
        if not po_row:
            frappe.throw(_("PO line {0} not found.").format(input_line.get("po_detail")))

        damaged = frappe.utils.flt(input_line.get("damaged_qty"))
        if damaged < 0:
            frappe.throw(_("Damaged qty cannot be negative for {0}.").format(po_row.item_code))
        if damaged > received:
            frappe.throw(
                _("Damaged qty ({0}) cannot exceed received qty ({1}) for {2}.")
                .format(damaged, received, po_row.item_code)
            )

        pending = (po_row.qty or 0) - (po_row.received_qty or 0)
        if received > pending:
            frappe.throw(
                _("Received qty {0} exceeds pending qty {1} for {2}.")
                .format(received, pending, po_row.item_code)
            )

        short_qty = pending - received
        short_reason = (input_line.get("short_reason") or "").strip()
        short_notes = (input_line.get("short_notes") or "").strip()

        # Require reason when short, if the feature is enabled
        if short_qty > 0 and capture_short and not short_reason:
            frappe.throw(_(
                "Short reason is required for {0} — {1} unit(s) short vs PO."
            ).format(po_row.item_code, short_qty))

        if damaged > 0 and not settings["default_rejected_warehouse"]:
            frappe.throw(_(
                "Damaged qty entered but no Default Rejected Warehouse "
                "is configured in WMS Settings."
            ))

        accepted = received - damaged

        # Target warehouse for accepted qty
        target_wh = input_line.get("warehouse") or po_row.warehouse or po.set_warehouse
        if _item_needs_qc(po_row.item_code) and settings["default_quarantine_warehouse"]:
            target_wh = settings["default_quarantine_warehouse"]

        pr.append("items", {
            "item_code": po_row.item_code,
            "item_name": po_row.item_name,
            "description": po_row.description,
            "uom": po_row.uom,
            "stock_uom": po_row.stock_uom,
            "conversion_factor": po_row.conversion_factor or 1,
            "qty": accepted,
            "rate": po_row.rate,
            "warehouse": target_wh,
            "purchase_order": po.name,
            # FIX: correct fieldname on Purchase Receipt Item. Previously used
            # "po_detail" (which is the Purchase Invoice Item field) — Frappe
            # silently dropped it, so ERPNext never updated the PO's received_qty,
            # allowing infinite over-receipts against the same PO.
            "purchase_order_item": po_row.name,
            "rejected_qty": damaged,
            "rejected_warehouse": settings["default_rejected_warehouse"] if damaged > 0 else None,
        })

        if short_qty > 0 and short_reason:
            shorts_to_record.append({
                "po_detail": po_row.name,
                "short_reason": short_reason,
                "short_notes": short_notes,
            })

        any_line_added = True

    if not any_line_added:
        frappe.throw(_("No lines to receive. Enter qty for at least one item."))

    pr.insert(ignore_permissions=True)
    pr.submit()

    # Write short-reason back to PO Item rows (post-submit, DB-level)
    if capture_short and shorts_to_record:
        _write_short_reasons(shorts_to_record)

    task_count = frappe.db.count("WMS Task", {
        "reference_doctype": "Purchase Receipt",
        "reference_name": pr.name,
    })

    return {
        "success": True,
        "purchase_receipt": pr.name,
        "task_count": task_count,
        "short_lines": len(shorts_to_record),
        "message": _("Receipt {0} created. {1} putaway task(s) queued.").format(pr.name, task_count),
    }


def _write_short_reasons(shorts):
    """
    Write short reason/notes to submitted PO Item rows via db.set_value.
    Child table rows can be updated even when the parent PO is submitted,
    because db.set_value bypasses the document's docstatus validation.

    Note: this targets `Purchase Order Item` directly by row name, so no
    fieldname ambiguity applies here — this helper was already correct.
    """
    for entry in shorts:
        frappe.db.set_value(
            "Purchase Order Item",
            entry["po_detail"],
            {
                "wms_short_reason": entry["short_reason"],
                "wms_short_notes": entry["short_notes"],
                "wms_short_captured_at": frappe.utils.now_datetime(),
                "wms_short_captured_by": frappe.session.user,
            },
            update_modified=False,
        )