import frappe
from frappe import _
from wms.wms.doctype.wms_settings.wms_settings import get_settings
from wms.api.putaway import require_supervisor



# Read endpoints
@frappe.whitelist()
def get_packable_delivery_notes(search=None):
    """
    Returns Draft DNs with packing progress, filtered by user's Company permissions.
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
            (SELECT COUNT(*) FROM `tabWMS Package` wp
            WHERE wp.delivery_note = dn.name
                AND wp.status != 'Cancelled'
                AND (wp.status = 'Sealed' OR wp.total_qty > 0)) AS package_count,
            (SELECT COUNT(*) FROM `tabWMS Package` wp
             WHERE wp.delivery_note = dn.name AND wp.status = 'Sealed') AS sealed_count
        FROM `tabDelivery Note` dn
        WHERE {where}
        ORDER BY dn.posting_date DESC, dn.name DESC
        LIMIT 50
    """, params, as_dict=True)

    # Enrich with packing progress and pick status
    for row in rows:
        status = _compute_dn_pack_status(row["name"])
        row["total_expected"] = status["total_expected"]
        row["total_packed"] = status["total_packed"]
        row["fully_packed"] = status["fully_packed"]
        row["pick_status"] = _dn_pick_status(row["name"])

    return rows


@frappe.whitelist()
def get_dn_packing_status(dn_name):
    """
    Returns per-item packing breakdown for a DN, plus existing packages.
    Used by the PackingStation screen.
    """
    dn = frappe.get_doc("Delivery Note", dn_name)
    if dn.docstatus != 0:
        frappe.throw(_("Only Draft Delivery Notes can be packed."))

    # Map of dn_detail -> packed qty (across all non-cancelled packages)
    packed_by_row = _packed_by_dn_row(dn_name)

    lines = []
    for item in dn.items:
        packed = packed_by_row.get(item.name, 0)
        lines.append({
            "dn_detail": item.name,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "uom": item.uom,
            "expected_qty": item.qty,
            "packed_qty": packed,
            "remaining_qty": max(0, item.qty - packed),
        })

    # Existing packages for this DN
    packages = frappe.get_all(
        "WMS Package",
        filters={"delivery_note": dn_name, "status": ["!=", "Cancelled"]},
        fields=["name", "package_type", "status", "total_qty", "total_items",
                "packed_by", "packed_at", "sealed_at"],
        order_by="creation asc",
    )

    total_expected = sum(item.qty for item in dn.items)
    total_packed = sum(l["packed_qty"] for l in lines)
    fully_packed = all(l["remaining_qty"] == 0 for l in lines)

    return {
        "name": dn.name,
        "customer": dn.customer,
        "customer_name": dn.customer_name,
        "company": dn.company,
        "posting_date": str(dn.posting_date),
        "lines": lines,
        "packages": packages,
        "total_expected": total_expected,
        "total_packed": total_packed,
        "fully_packed": fully_packed,
    }


@frappe.whitelist()
def get_package_details(package_name):
    """
    Returns full package state — items, totals, status.
    Used by the PackingStation when a package is active.
    """
    package = frappe.get_doc("WMS Package", package_name)

    items = []
    for pi in package.package_items:
        items.append({
            "item_code": pi.item_code,
            "item_name": pi.item_name,
            "qty": pi.qty,
            "uom": pi.uom,
            "dn_detail": pi.dn_detail,
            "scanned_by": pi.scanned_by,
            "scanned_at": str(pi.scanned_at) if pi.scanned_at else None,
        })

    return {
        "name": package.name,
        "delivery_note": package.delivery_note,
        "customer": package.customer,
        "company": package.company,
        "package_type": package.package_type,
        "status": package.status,
        "total_qty": package.total_qty or 0,
        "total_items": package.total_items or 0,
        "packed_by": package.packed_by,
        "packed_at": str(package.packed_at) if package.packed_at else None,
        "sealed_at": str(package.sealed_at) if package.sealed_at else None,
        "notes": package.notes or "",
        "items": items,
    }


# Write endpoints
@frappe.whitelist()
def start_package(dn_name, package_type="Carton"):
    """
    Creates a new Open WMS Package linked to the DN.
    Returns the new package.
    """
    dn = frappe.get_doc("Delivery Note", dn_name)
    if dn.docstatus != 0:
        frappe.throw(_("Only Draft Delivery Notes can be packed."))

    # NEW: refuse if already fully packed
    status = _compute_dn_pack_status(dn_name)
    if status["fully_packed"]:
        frappe.throw(_(
            "All items on this Delivery Note are already packed. "
            "No new package needed."
        ))

    if package_type not in ("Carton", "Pallet", "Envelope", "Bag", "Other"):
        frappe.throw(_("Invalid package type: {0}").format(package_type))

    package = frappe.get_doc({
        "doctype": "WMS Package",
        "delivery_note": dn.name,
        "customer": dn.customer,
        "company": dn.company,
        "posting_date": frappe.utils.today(),
        "package_type": package_type,
        "status": "Open",
        "packed_by": frappe.session.user,
        "packed_at": frappe.utils.now_datetime(),
    })
    package.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "package_name": package.name,
        "message": _("Package {0} started.").format(package.name),
    }


@frappe.whitelist()
def scan_item_to_package(package_name, item_code, qty=1, dn_detail=None):
    """
    Verifies the item belongs on the DN, that adding qty won't exceed the
    DN's expected qty (across all packages), and adds it to the package.
    """
    qty = frappe.utils.flt(qty)
    if qty <= 0:
        frappe.throw(_("Qty must be greater than zero."))

    package = frappe.get_doc("WMS Package", package_name)
    if package.status != "Open":
        frappe.throw(_(
            "Package {0} is {1}. Only Open packages can receive items."
        ).format(package.name, package.status))

    dn = frappe.get_doc("Delivery Note", package.delivery_note)
    if dn.docstatus != 0:
        frappe.throw(_("Delivery Note is no longer Draft."))

    # Packed qty per DN row (excluding current package's own items being replaced)
    packed_by_row = _packed_by_dn_row(dn.name, exclude_package=package.name)
    # Add current package's items back so we account for what's already here
    for pi in package.package_items:
        packed_by_row[pi.dn_detail] = packed_by_row.get(pi.dn_detail, 0) + pi.qty

    # Find a DN row for this item that has capacity
    target_row = None
    for item in dn.items:
        if item.item_code != item_code:
            continue
        if dn_detail and item.name != dn_detail:
            continue
        already = packed_by_row.get(item.name, 0)
        if already + qty <= item.qty:
            target_row = item
            break
        if already < item.qty:
            remaining = item.qty - already
            frappe.throw(_(
                "Cannot scan {0} unit(s) of {1}: only {2} remaining on DN."
            ).format(qty, item_code, remaining))

    if not target_row:
        frappe.throw(_(
            "Item {0} is not on this Delivery Note, or its full qty is already packed."
        ).format(item_code))

    # Check if this dn_detail already has a row in this package
    existing_row = None
    for pi in package.package_items:
        if pi.dn_detail == target_row.name:
            existing_row = pi
            break

    if existing_row:
        existing_row.qty = (existing_row.qty or 0) + qty
    else:
        package.append("package_items", {
            "item_code": item_code,
            "item_name": target_row.item_name,
            "qty": qty,
            "uom": target_row.uom,
            "dn_detail": target_row.name,
            "scanned_by": frappe.session.user,
            "scanned_at": frappe.utils.now_datetime(),
        })

    _recompute_package_totals(package)
    package.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "package_name": package.name,
        "total_qty": package.total_qty,
        "total_items": package.total_items,
        "message": _("Added {0} × {1} to {2}.").format(qty, item_code, package.name),
    }


@frappe.whitelist()
def seal_package(package_name):
    """
    Locks the package: sets status=Sealed, records sealer and timestamp,
    freezes items (no further edits until unsealed by a supervisor).
    """
    package = frappe.get_doc("WMS Package", package_name)

    if package.status != "Open":
        frappe.throw(_("Only Open packages can be sealed. This one is {0}.").format(package.status))

    if not package.package_items:
        frappe.throw(_("Cannot seal an empty package."))

    _recompute_package_totals(package)
    package.status = "Sealed"
    package.sealed_by = frappe.session.user
    package.sealed_at = frappe.utils.now_datetime()
    package.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "package_name": package.name,
        "total_qty": package.total_qty,
        "message": _("Package {0} sealed with {1} unit(s).").format(
            package.name, package.total_qty
        ),
    }


@frappe.whitelist()
def unseal_package(package_name):
    """
    Supervisor-only: reverts a Sealed package to Open so items can be added/removed.
    """
    require_supervisor()

    package = frappe.get_doc("WMS Package", package_name)
    if package.status != "Sealed":
        frappe.throw(_("Only Sealed packages can be unsealed."))

    package.status = "Open"
    package.sealed_by = None
    package.sealed_at = None
    package.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": _("Package {0} reopened.").format(package.name),
    }


@frappe.whitelist()
def delete_package(package_name):
    """
    Deletes a WMS Package.
      - Empty Open packages: anyone can delete (no side effects)
      - Non-empty or Sealed: supervisor required (supervisor must unseal first)
    """
    package = frappe.get_doc("WMS Package", package_name)

    if package.status != "Open":
        frappe.throw(_(
            "Only Open packages can be deleted. Unseal or cancel first."
        ))

    # Non-empty Open packages need supervisor oversight
    if package.package_items:
        require_supervisor()

    dn_name = package.delivery_note
    package.delete(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": _("Package deleted from DN {0}.").format(dn_name),
    }


# DN submit guard
def validate_dn_pack_before_submit(doc, method):
    """
    Runs on Delivery Note.before_submit.

    Strict mode (setting ON): blocks submit unless every item is packed
    AND every package is Sealed.

    Lenient mode (setting OFF): no-op. The on_submit hook auto-seals any
    Open packages so they don't become orphaned.
    """
    settings = get_settings()
    if not settings.get("require_pack_before_dn_submit"):
        return  # lenient mode

    # Check 1: every DN item is fully packed
    status = _compute_dn_pack_status(doc.name)
    if not status["fully_packed"]:
        missing = status["total_expected"] - status["total_packed"]
        frappe.throw(_(
            "Cannot submit this Delivery Note: {0} unit(s) not yet packed. "
            "Pack all items before submitting."
        ).format(missing))

    # Check 2: no Open packages remain — every container must be Sealed
    open_packages = frappe.get_all(
        "WMS Package",
        filters={"delivery_note": doc.name, "status": "Open"},
        pluck="name",
    )
    if open_packages:
        frappe.throw(_(
            "Cannot submit this Delivery Note: {0} package(s) are still Open. "
            "Seal them first: {1}"
        ).format(len(open_packages), ", ".join(open_packages)))



# Helpers
def _packed_by_dn_row(dn_name, exclude_package=None):
    """
    Returns {dn_detail: packed_qty} summing all package items across
    non-cancelled packages for the given DN. Optionally excludes one package.
    """
    filters = {
        "delivery_note": dn_name,
        "status": ["!=", "Cancelled"],
    }
    if exclude_package:
        filters["name"] = ["!=", exclude_package]

    package_names = frappe.get_all("WMS Package", filters=filters, pluck="name")
    if not package_names:
        return {}

    result = {}
    rows = frappe.get_all(
        "WMS Package Item",
        filters={"parent": ["in", package_names]},
        fields=["dn_detail", "qty"],
    )
    for r in rows:
        if not r.dn_detail:
            continue
        result[r.dn_detail] = result.get(r.dn_detail, 0) + (r.qty or 0)

    return result


def _recompute_package_totals(package):
    """Sum qty and count distinct items from package_items."""
    total_qty = 0
    for pi in package.package_items:
        total_qty += pi.qty or 0
    package.total_qty = total_qty
    package.total_items = len(package.package_items)


def _compute_dn_pack_status(dn_name):
    """
    Aggregate packing state for a DN:
      total_expected = sum of DN item qty
      total_packed   = sum of package items across non-cancelled packages
      fully_packed   = bool
    """
    dn = frappe.get_doc("Delivery Note", dn_name)
    total_expected = sum((item.qty or 0) for item in dn.items)

    packed_by_row = _packed_by_dn_row(dn_name)
    total_packed = sum(packed_by_row.values())

    fully_packed = True
    for item in dn.items:
        packed = packed_by_row.get(item.name, 0)
        if packed < (item.qty or 0):
            fully_packed = False
            break

    return {
        "total_expected": total_expected,
        "total_packed": total_packed,
        "fully_packed": fully_packed,
    }


def _dn_pick_status(dn_name):
    """
    'Not Released' if no pick tasks, 'In Progress' if any Open/Exception,
    'Picked' if all pick tasks completed (or cancelled), else 'Pending'.
    """
    total = frappe.db.count("WMS Task", {"task_type": "Pick", "delivery_note": dn_name})
    if total == 0:
        return "Not Released"

    open_or_exc = frappe.db.count("WMS Task", {
        "task_type": "Pick",
        "delivery_note": dn_name,
        "status": ["in", ["Open", "Exception"]],
    })
    if open_or_exc:
        return "In Progress"

    return "Picked"

def cancel_dn_packages(doc, method):
    """
    Hook on Delivery Note.before_cancel.
    Cancels all non-cancelled packages linked to this DN.
    """
    packages = frappe.get_all(
        "WMS Package",
        filters={"delivery_note": doc.name, "status": ["!=", "Cancelled"]},
        pluck="name",
    )
    for p in packages:
        frappe.db.set_value("WMS Package", p, "status", "Cancelled",
                            update_modified=False)
    if packages:
        frappe.db.commit()


def seal_dn_packages_on_submit(doc, method):
    """
    Runs on Delivery Note.on_submit.

    Lenient mode (setting OFF): auto-seals any Open packages so a DN
    can never submit with orphaned Open containers.

    Strict mode (setting ON): no-op — before_submit already blocked
    submit if any package was unsealed.
    """
    settings = get_settings()
    if settings.get("require_pack_before_dn_submit"):
        return

    packages = frappe.get_all(
        "WMS Package",
        filters={"delivery_note": doc.name, "status": "Open"},
        pluck="name",
    )
    if not packages:
        return

    sealed_at = frappe.utils.now_datetime()
    for p in packages:
        frappe.db.set_value("WMS Package", p, {
            "status": "Sealed",
            "sealed_by": frappe.session.user,
            "sealed_at": sealed_at,
        }, update_modified=False)

    frappe.db.commit()

    frappe.msgprint(
        _("{0} package(s) auto-sealed on submit.").format(len(packages)),
        indicator="green",
        alert=True,
    )