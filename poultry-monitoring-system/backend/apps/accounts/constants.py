"""Role definitions and their Django-group/permission mapping.

Roles are implemented as Django Groups so they integrate with the standard
permission framework, the admin, and ``user.has_perm``. ``CustomUser.role``
mirrors the *primary* role for convenient querying and template logic, but all
authorization decisions ultimately consult group membership / permissions.
"""

ROLE_ADMIN = "ADMIN"
ROLE_OWNER = "OWNER"
ROLE_MANAGER = "MANAGER"
ROLE_WORKER = "WORKER"
ROLE_VET = "VET"

ROLE_CHOICES = [
    (ROLE_ADMIN, "System Administrator"),
    (ROLE_OWNER, "Farm Owner"),
    (ROLE_MANAGER, "Farm Manager"),
    (ROLE_WORKER, "Farm Worker"),
    (ROLE_VET, "Veterinary Consultant / Viewer"),
]

# Group names map 1:1 to role codes.
ALL_ROLES = [code for code, _ in ROLE_CHOICES]

# Capability flags resolved from role membership. Used for fine-grained
# template/view checks beyond raw model permissions.
ROLE_CAPABILITIES = {
    ROLE_ADMIN: {
        "manage_users", "manage_roles", "manage_farms", "register_devices",
        "global_settings", "view_logs", "view_all_reports", "view_finance",
        "manage_records", "manage_health", "manage_inventory", "resolve_alerts",
        "review_predictions", "approve_adjustments",
    },
    ROLE_OWNER: {
        "view_all_reports", "view_finance", "manage_users", "resolve_alerts",
        "approve_adjustments", "review_predictions", "manage_farms",
        "register_devices",
    },
    ROLE_MANAGER: {
        "manage_records", "manage_health", "manage_inventory", "view_finance",
        "resolve_alerts", "view_all_reports", "review_predictions",
    },
    ROLE_WORKER: {
        "record_mortality", "record_feed", "record_observations",
        "view_assigned_alerts",
    },
    ROLE_VET: {
        "view_health", "view_environment", "review_predictions", "add_comments",
        "view_all_reports",
    },
}


def role_has_capability(role: str, capability: str) -> bool:
    return capability in ROLE_CAPABILITIES.get(role, set())
