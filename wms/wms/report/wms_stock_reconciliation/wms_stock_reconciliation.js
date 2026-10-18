// Copyright (c) 2026, Gautam Tyagi and contributors
// For license information, please see license.txt

// Compatible with Frappe v15 and v16.

frappe.query_reports["WMS Stock Reconciliation"] = {
    filters: [
        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            options: "Warehouse",
        },
        {
            fieldname: "item_code",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item",
        },
        {
            fieldname: "only_drift",
            label: __("Only Show Drift"),
            fieldtype: "Check",
            default: 0,
        },
    ],

    onload: function () {
        wms_inject_css();
        wms_bind_card_actions();
    },

    after_datatable_render: function () {
        wms_fix_icons();
        setTimeout(wms_fix_icons, 300);
        setTimeout(wms_fix_icons, 800);
    },

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        if (column.fieldname === "status") {
            const is_ok = data.status === "OK";
            const color = is_ok ? "#29a36a" : "#e24c4c";
            const label = frappe.utils.escape_html(is_ok ? __("OK") : __("Drift"));
            return `<span style="display:inline-flex;align-items:center;gap:6px;padding:2px 10px;
                        border-radius:99px;font-size:12px;font-weight:600;
                        color:${color};background:${color}22;">
                        <span style="width:6px;height:6px;border-radius:50%;background:${color};"></span>${label}
                    </span>`;
        }

        if (column.fieldname === "diff") {
            const diff = flt(data.diff);
            let color = "var(--text-muted)";
            if (diff <= -0.001) color = "#e24c4c";
            else if (diff >= 0.001) color = "#f59e0b";
            return `<span style="color:${color};font-weight:600;">${value}</span>`;
        }

        return value;
    },
};
x
function wms_bind_card_actions() {
    $(document)
        .off(".wmsrecon")
        .on("click.wmsrecon keydown.wmsrecon", ".wms-card.wms-clickable", function (e) {
            if (e.type === "keydown") {
                if (e.key !== "Enter" && e.key !== " ") return;
                e.preventDefault();
            }
            if (!frappe.query_report || frappe.query_report.report_name !== "WMS Stock Reconciliation") return;

            const only_drift = $(this).hasClass("wms-action-drift") ? 1 : 0;
            frappe.query_report.set_filter_value("only_drift", only_drift);
        });
}

// If the SVG icons were stripped by Frappe's HTML sanitiser, fall back to emoji.
// Keys must match ICONS in the Python file.
const WMS_EMOJI = { box: "📦", warning: "⚠️", scale: "⚖️", truck: "🚚", target: "🎯" };

function wms_fix_icons() {
    $(".wms-card .wms-icon").each(function () {
        const $el = $(this);
        if ($el.find("svg").length) return;
        const match = ($el.attr("class") || "").match(/wms-icon-(\w+)/);
        if (match && WMS_EMOJI[match[1]]) $el.text(WMS_EMOJI[match[1]]);
    });
}

// Hover / focus styles (inline styles can't do :hover or :focus-visible)
function wms_inject_css() {
    if ($("#wms-summary-css").length) return;
    $(`<style id="wms-summary-css">
        .wms-card.wms-clickable:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md) !important;
        }
        .wms-card.wms-clickable:focus-visible {
            outline: 2px solid var(--primary, #2490ef);
            outline-offset: 2px;
        }
    </style>`).appendTo("head");
}