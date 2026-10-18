# Copyright (c) 2026, Gautam Tyagi and contributors
# For license information, please see license.txt

from html import escape

import frappe
from frappe import _

DRIFT_TOLERANCE = 0.001


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)

    enrich_item_names(data)

    for row in data:
        row["status"] = "OK" if abs(row["diff"] or 0) < DRIFT_TOLERANCE else "Drift"

    # Summary is calculated on ALL rows (before "Only Show Drift" is applied),
    # so the cards always reflect the full reconciliation picture.
    summary_html = get_summary_html(data, filters)

    if filters.get("only_drift"):
        data = [row for row in data if abs(row["diff"] or 0) >= DRIFT_TOLERANCE]

    return columns, data, summary_html, None, None


def _svg(paths):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{paths}</svg>'
    )


# Icon keys must match WMS_EMOJI in the JS file (used as a fallback if SVG is stripped)
ICONS = {
    "box": _svg('<path d="M21 8l-9-5-9 5v8l9 5 9-5V8z"/><path d="M3.3 7.5L12 12.5l8.7-5"/><path d="M12 22V12.5"/>'),
    "warning": _svg(
        '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>'
        '<path d="M12 9v4"/><path d="M12 17h.01"/>'
    ),
    "scale": _svg(
        '<path d="M4 6h10"/><path d="M18 6h2"/><circle cx="16" cy="6" r="2"/>'
        '<path d="M4 12h2"/><path d="M10 12h10"/><circle cx="8" cy="12" r="2"/>'
        '<path d="M4 18h12"/><circle cx="18" cy="18" r="2"/>'
    ),
    "truck": _svg(
        '<path d="M1 6h13v11H1z"/><path d="M14 10h4l3 3v4h-7z"/>'
        '<circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>'
    ),
    "target": _svg('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>'),
}


def get_summary_html(data, filters=None):
    filters = filters or {}
    only_drift = bool(filters.get("only_drift"))

    total_count = len(data)
    drift_count = sum(1 for row in data if abs(row["diff"] or 0) >= DRIFT_TOLERANCE)
    net_drift_qty = sum(row["diff"] or 0 for row in data)
    picked_qty = sum(row["picked_not_shipped"] or 0 for row in data)
    accuracy = round((total_count - drift_count) / total_count * 100, 1) if total_count else None

    BLUE, RED, GREEN, ORANGE, CYAN, GREY = "#2490ef", "#e24c4c", "#29a36a", "#f59e0b", "#06b6d4", "#8d99a6"

    if accuracy is None:
        accuracy_color = GREY
    elif drift_count == 0:
        accuracy_color = GREEN
    elif accuracy >= 95:
        accuracy_color = ORANGE
    else:
        accuracy_color = RED

    # "action" makes a card clickable (handled by class name in the JS file)
    cards = [
        {
            "icon": "box", "label": _("Items Total"), "value": f"{total_count:,}",
            "caption": _("Click to show all items"), "color": BLUE,
            "action": "all", "active": not only_drift,
        },
        {
            "icon": "warning", "label": _("Items with Drift"), "value": f"{drift_count:,}",
            "caption": _("Click to show only drift"),
            "color": RED if drift_count else (GREEN if total_count else GREY),
            "action": "drift", "active": only_drift,
        },
        {
            "icon": "scale", "label": _("Net Drift Qty"), "value": f"{net_drift_qty:,.2f}",
            "caption": _("WMS total minus ERPNext qty"),
            "color": ORANGE if abs(net_drift_qty) >= DRIFT_TOLERANCE else GREEN,
        },
        {
            "icon": "truck", "label": _("Picked (not shipped)"), "value": f"{picked_qty:,.2f}",
            "caption": _("Awaiting Delivery Note submit"), "color": CYAN,
        },
        {
            "icon": "target", "label": _("Stock Accuracy"),
            "value": f"{accuracy:.1f}%" if accuracy is not None else "N/A",
            "caption": _("Items matching ERPNext stock") if accuracy is not None else _("No items to reconcile"),
            "color": accuracy_color, "progress": accuracy,
        },
    ]

    card_html = ""
    for c in cards:
        color = c["color"]
        action = c.get("action")
        label = escape(str(c["label"]))
        caption = escape(str(c["caption"]))

        css_class = "wms-card"
        a11y = ""
        if action:
            css_class += f" wms-clickable wms-action-{action}"
            a11y = f'role="button" tabindex="0" aria-label="{label}"'

        shadow = f"box-shadow:0 0 0 2px {color};" if c.get("active") else "box-shadow:var(--shadow-sm);"
        cursor = "cursor:pointer;" if action else ""

        progress_html = ""
        if c.get("progress") is not None:
            pct = max(0, min(100, c["progress"]))
            progress_html = (
                f'<div style="height:6px;border-radius:99px;background:{color}22;margin-top:12px;overflow:hidden;">'
                f'<div style="width:{pct}%;height:100%;background:{color};border-radius:99px;"></div></div>'
            )

        card_html += f"""
        <div class="{css_class}" {a11y}
             style="flex:1 1 200px;min-width:200px;background:var(--card-bg,#fff);
                    border:1px solid var(--border-color,#e2e6ea);border-top:4px solid {color};
                    border-radius:12px;padding:16px 18px;text-align:start;{shadow}{cursor}
                    transition:transform .15s ease, box-shadow .15s ease;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div class="wms-icon wms-icon-{c["icon"]}"
                     style="width:34px;height:34px;border-radius:9px;background:{color}22;color:{color};
                            display:flex;align-items:center;justify-content:center;font-size:17px;
                            line-height:1;flex-shrink:0;">{ICONS[c["icon"]]}</div>
                <div style="font-size:13px;font-weight:500;color:var(--text-muted,#6c7680);">{label}</div>
            </div>
            <div style="font-size:30px;font-weight:700;line-height:1.25;margin:12px 0 4px;color:{color};">
                <bdi>{c["value"]}</bdi>
            </div>
            <div style="font-size:12px;color:var(--text-muted,#8d99a6);">{caption}</div>
            {progress_html}
        </div>"""

    return f'''<div style="display:flex;flex-wrap:wrap;gap:14px;margin:4px 0 12px;">{card_html}</div>'''


def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 180},
        {"label": _("Bins Qty"), "fieldname": "bins_qty", "fieldtype": "Float", "width": 100, "precision": 2},
        {"label": _("Open Tasks"), "fieldname": "open_qty", "fieldtype": "Float", "width": 100, "precision": 2},
        {"label": _("Exception Tasks"), "fieldname": "exc_qty", "fieldtype": "Float", "width": 120, "precision": 2},
        {"label": _("WMS Total"), "fieldname": "wms_total", "fieldtype": "Float", "width": 110, "precision": 2},
        {"label": _("ERPNext Qty"), "fieldname": "erpnext_qty", "fieldtype": "Float", "width": 110, "precision": 2},
        {"label": _("Diff"), "fieldname": "diff", "fieldtype": "Float", "width": 90, "precision": 2},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
        {"label": _("Picked (not shipped)"), "fieldname": "picked_not_shipped", "fieldtype": "Float", "width": 140, "precision": 2},
    ]


def get_data(filters):
    conditions = []
    params = {}

    if filters.get("warehouse"):
        conditions.append("combo.warehouse = %(warehouse)s")
        params["warehouse"] = filters["warehouse"]

    if filters.get("item_code"):
        conditions.append("combo.item_code = %(item_code)s")
        params["item_code"] = filters["item_code"]

    condition_clause = ""
    if conditions:
        condition_clause = "AND " + " AND ".join(conditions)

    query = f"""
        SELECT
            combo.item_code,
            combo.warehouse,
            COALESCE(w.bins_qty, 0) AS bins_qty,
            COALESCE(w.open_qty, 0) AS open_qty,
            COALESCE(w.exc_qty, 0)  AS exc_qty,
            COALESCE(p.picked_not_shipped, 0) AS picked_not_shipped,
            (
                COALESCE(w.bins_qty, 0)
                + COALESCE(w.open_qty, 0)
                + COALESCE(w.exc_qty, 0)
                + COALESCE(p.picked_not_shipped, 0)
            ) AS wms_total,
            COALESCE(b.actual_qty, 0) AS erpnext_qty,
            (
                (
                    COALESCE(w.bins_qty, 0)
                    + COALESCE(w.open_qty, 0)
                    + COALESCE(w.exc_qty, 0)
                    + COALESCE(p.picked_not_shipped, 0)
                )
                - COALESCE(b.actual_qty, 0)
            ) AS diff
        FROM (
            SELECT item_code, warehouse FROM `tabBin` WHERE actual_qty != 0
            UNION
            SELECT current_item AS item_code, warehouse FROM `tabWMS Bin Location`
                WHERE current_item IS NOT NULL AND current_item != ''
            UNION
            SELECT item_code, warehouse FROM `tabWMS Task`
                WHERE task_type = 'Putaway' AND status IN ('Open', 'Exception')
            UNION
            SELECT item_code, warehouse FROM `tabWMS Task`
                WHERE task_type = 'Pick' AND status = 'Completed'
                  AND delivery_note IS NOT NULL
        ) AS combo

        LEFT JOIN (
            SELECT
                item_code,
                warehouse,
                SUM(bins_qty) AS bins_qty,
                SUM(open_qty) AS open_qty,
                SUM(exc_qty)  AS exc_qty
            FROM (
                SELECT
                    current_item AS item_code,
                    warehouse,
                    SUM(qty_in_bin) AS bins_qty,
                    0 AS open_qty,
                    0 AS exc_qty
                FROM `tabWMS Bin Location`
                WHERE current_item IS NOT NULL AND current_item != ''
                GROUP BY current_item, warehouse

                UNION ALL

                SELECT
                    item_code,
                    warehouse,
                    0 AS bins_qty,
                    SUM(CASE WHEN status = 'Open' THEN qty ELSE 0 END) AS open_qty,
                    SUM(CASE WHEN status = 'Exception' THEN qty ELSE 0 END) AS exc_qty
                FROM `tabWMS Task`
                WHERE task_type = 'Putaway'
                GROUP BY item_code, warehouse
            ) AS inner_wms
            GROUP BY item_code, warehouse
        ) AS w
            ON w.item_code = combo.item_code AND w.warehouse = combo.warehouse

        LEFT JOIN (
            SELECT
                wt.item_code,
                wt.warehouse,
                SUM(wt.picked_qty) AS picked_not_shipped
            FROM `tabWMS Task` wt
            INNER JOIN `tabDelivery Note` dn ON dn.name = wt.delivery_note
            WHERE wt.task_type = 'Pick'
              AND wt.status = 'Completed'
              AND dn.docstatus = 0
            GROUP BY wt.item_code, wt.warehouse
        ) AS p
            ON p.item_code = combo.item_code AND p.warehouse = combo.warehouse

        LEFT JOIN `tabBin` b
            ON b.item_code = combo.item_code AND b.warehouse = combo.warehouse

        WHERE 1=1
        {condition_clause}
        ORDER BY combo.item_code, combo.warehouse
    """

    return frappe.db.sql(query, params, as_dict=True)


def enrich_item_names(data):
    if not data:
        return
    item_codes = list({row["item_code"] for row in data if row.get("item_code")})
    if not item_codes:
        return
    names = dict(frappe.get_all(
        "Item",
        filters={"name": ["in", item_codes]},
        fields=["name", "item_name"],
        as_list=True,
    ))
    for row in data:
        row["item_name"] = names.get(row["item_code"], "")