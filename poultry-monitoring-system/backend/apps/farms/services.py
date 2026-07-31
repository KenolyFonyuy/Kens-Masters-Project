"""Farm visibility / data-isolation helpers."""
from .models import Farm


def farms_for_user(user):
    """Return the queryset of farms a user is permitted to see.

    * Superusers / ADMIN: all farms.
    * OWNER: farms they own.
    * Others (MANAGER / WORKER / VET): farms explicitly assigned to them.
    """
    if not user.is_authenticated:
        return Farm.objects.none()
    if user.is_superuser or user.has_role("ADMIN"):
        return Farm.objects.all()
    if user.has_role("OWNER"):
        return Farm.objects.filter(owner=user) | user.assigned_farms.all()
    return user.assigned_farms.all()


def user_can_access_farm(user, farm) -> bool:
    if user.is_superuser or user.has_role("ADMIN"):
        return True
    return farms_for_user(user).filter(pk=farm.pk).exists()
