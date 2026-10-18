# Copyright (c) 2026, Gautam Tyagi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WMSSettings(Document):
    pass


@frappe.whitelist()
def get_settings():
    """
    Return WMS Settings as a plain dict with fallbacks applied.
    Call this from other modules instead of frappe.get_single directly,
    so defaults are always consistent.
    """
    settings = frappe.get_single("WMS Settings")

    allow_partial = settings.allow_partial_bin_fill
    if allow_partial is None:
        allow_partial = True

    return {
        "receiving_mode": settings.receiving_mode or "Standard ERPNext Only",
        "enable_qc_hold_gate": bool(settings.enable_qc_hold_gate_hard),
        "default_quarantine_warehouse": settings.default_quarantine_warehouse or None,
        "default_rejected_warehouse": settings.default_rejected_warehouse or None,
        "allow_partial_bin_fill": bool(allow_partial),
        "default_bin_capacity": settings.default_bin_capacity or 0,
        "excluded_bin_types": [
            row.bin_type for row in (settings.exclude_bin_types_from_suggestion or [])
        ],
        "wms_supervisor_role": settings.wms_supervisor_role or "WMS Supervisor",
        "capture_short_receipt_reason": bool(settings.capture_short_receipt_reason),
        "require_item_scan_on_pick": bool(settings.require_item_scan_on_pick),
        "pick_release_mode": settings.pick_release_mode or "Manual Release",
        "require_pack_before_dn_submit": bool(settings.require_pack_before_dn_submit),
    }
