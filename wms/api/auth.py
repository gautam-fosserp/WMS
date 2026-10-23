import frappe
from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
from frappe.utils.password import get_decrypted_password


@frappe.whitelist(allow_guest=True)
def get_social_logins():
    """Enabled Social Login Keys (Google, etc.) for the WMS login page.

    Mirrors what Frappe's own /login page builds, but returns JSON so the
    Vue login screen can render the buttons. A misconfigured provider is
    skipped (and logged) instead of breaking the whole call.
    """
    redirect_to = "/wms-mobile/"
    providers = frappe.get_all(
        "Social Login Key",
        filters={"enable_social_login": 1},
        fields=["name", "client_id", "base_url", "provider_name"],
        order_by="name",
    )

    result = []
    for p in providers:
        try:
            client_secret = get_decrypted_password(
                "Social Login Key", p.name, "client_secret", raise_exception=False
            )
            if not (client_secret and p.client_id and p.base_url):
                continue
            if not get_oauth_keys(p.name):
                continue
            result.append(
                {
                    "name": p.name,
                    "provider_name": p.provider_name,
                    "auth_url": get_oauth2_authorize_url(p.name, redirect_to),
                }
            )
        except Exception:
            frappe.clear_messages()
            frappe.log_error(
                title=f"WMS social login: skipped provider {p.name}",
                message=frappe.get_traceback(),
            )
    return result