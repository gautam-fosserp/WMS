import frappe
import os
import glob


def get_context(context):
    context.no_cache = 1

    frontend_dir = frappe.get_app_path("wms", "public", "frontend", "assets")
    js_files = glob.glob(os.path.join(frontend_dir, "index.*.js"))
    css_files = glob.glob(os.path.join(frontend_dir, "index.*.css"))

    context.js_path = f"/assets/wms/frontend/assets/{os.path.basename(js_files[0])}" if js_files else ""
    context.css_path = f"/assets/wms/frontend/assets/{os.path.basename(css_files[0])}" if css_files else ""