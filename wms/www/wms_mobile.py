import frappe
import os
import glob


def get_context(context):
    context.no_cache = 1

    assets_dir = frappe.get_app_path("wms", "public", "frontend", "assets")
    base = "/assets/wms/frontend/assets/"

    js_files = glob.glob(os.path.join(assets_dir, "index.*.js"))
    css_files = sorted(
        glob.glob(os.path.join(assets_dir, "vendor.*.css"))
        + glob.glob(os.path.join(assets_dir, "index.*.css"))
    )

    context.js_path = base + os.path.basename(js_files[0]) if js_files else ""
    context.css_paths = [base + os.path.basename(f) for f in css_files]
