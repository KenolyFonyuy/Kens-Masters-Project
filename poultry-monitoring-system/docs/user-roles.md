# User-Role Guide

Roles are Django Groups; `CustomUser.role` mirrors the primary group.
Authorization is enforced in views, querysets, API permissions and templates.

| Capability | Admin | Owner | Manager | Worker | Vet/Viewer |
|---|:---:|:---:|:---:|:---:|:---:|
| Manage users / roles | ✓ | ✓ (users) | | | |
| Manage farms | ✓ | ✓ | | | |
| Register IoT devices | ✓ | ✓ | | | |
| Manage batches / records | ✓ | ✓ | ✓ | | |
| Record mortality / feed / observations | ✓ | ✓ | ✓ | ✓ | |
| Health observations / treatments | ✓ | ✓ | ✓ | view+add obs | view + comment |
| Inventory | ✓ | ✓ | ✓ | view | |
| Finance (expenses/sales) | ✓ | ✓ | ✓ | **no** | **no** |
| Resolve alerts | ✓ | ✓ | ✓ | view assigned | view |
| Review vision predictions | ✓ | ✓ | ✓ | | ✓ |
| Reports | all | all | operational+finance | | health/env/vision |
| Audit log | ✓ | ✓ | | | |

Farm data isolation: non-admins only see farms they own (owner) or are assigned
to (manager/worker/vet). `farms_for_user()` scopes every list/detail queryset.

Run `python manage.py setup_roles` after migrations to (re)create groups and
permissions. It is idempotent.
