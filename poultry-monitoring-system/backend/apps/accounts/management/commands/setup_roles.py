"""Create role groups and grant model permissions per role.

Idempotent — safe to run after every migration/deploy.

Permission policy (high level):
  ADMIN   : superuser-style, all permissions.
  OWNER   : full view across the org + finance + manage users; change/add on
            most operational records; review alerts.
  MANAGER : add/change/view on operational + finance + inventory + health.
  WORKER  : add/view on mortality, feed usage, daily/health observations only.
  VET     : view health + environment + vision; add health comments/observations.
"""
from apps.accounts.constants import ALL_ROLES
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Apps whose models are "operational records".
OPERATIONAL_APPS = [
    "farms", "flocks", "feeding", "health", "inventory", "finance",
    "iot", "vision", "alerts",
]
FINANCE_APPS = ["finance"]
HEALTH_APPS = ["health"]


def perms_for_apps(app_labels, actions=None):
    qs = Permission.objects.filter(content_type__app_label__in=app_labels)
    if actions:
        from django.db.models import Q

        q = Q()
        for action in actions:
            q |= Q(codename__startswith=f"{action}_")
        qs = qs.filter(q)
    return qs


class Command(BaseCommand):
    help = "Create role groups and assign permissions (idempotent)."

    def handle(self, *args, **options):
        groups = {}
        for role in ALL_ROLES:
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.clear()
            groups[role] = group

        # ADMIN: everything.
        groups["ADMIN"].permissions.set(Permission.objects.all())

        # OWNER: view everything, change/add operational, manage users, finance.
        owner_perms = set(perms_for_apps(OPERATIONAL_APPS + ["accounts", "audit"], ["view"]))
        owner_perms |= set(perms_for_apps(OPERATIONAL_APPS, ["add", "change"]))
        owner_perms |= set(perms_for_apps(["accounts"], ["add", "change"]))
        groups["OWNER"].permissions.set(owner_perms)

        # MANAGER: add/change/view operational + finance + inventory + health.
        manager_perms = set(
            perms_for_apps(OPERATIONAL_APPS, ["view", "add", "change"])
        )
        groups["MANAGER"].permissions.set(manager_perms)

        # WORKER: limited add/view.
        worker_perms = set(
            perms_for_apps(
                ["flocks", "feeding", "health"], ["view", "add"]
            )
        )
        # Workers may view farms/pens/batches they are assigned to.
        worker_perms |= set(perms_for_apps(["farms"], ["view"]))
        worker_perms |= set(perms_for_apps(["alerts"], ["view"]))
        groups["WORKER"].permissions.set(worker_perms)

        # VET: view health/environment/vision; add health observations.
        vet_perms = set(perms_for_apps(HEALTH_APPS, ["view", "add"]))
        vet_perms |= set(perms_for_apps(["iot", "vision", "alerts"], ["view"]))
        vet_perms |= set(perms_for_apps(["farms", "flocks"], ["view"]))
        groups["VET"].permissions.set(vet_perms)

        self.stdout.write(
            self.style.SUCCESS(
                "Roles configured: "
                + ", ".join(
                    f"{r}({groups[r].permissions.count()} perms)" for r in ALL_ROLES
                )
            )
        )
