"""Custom user model, profile, and role helpers."""
import uuid

from django.contrib.auth.models import AbstractUser, Group
from django.db import models

from .constants import ROLE_CHOICES, ROLE_WORKER, role_has_capability
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """Project user. ``role`` mirrors the primary Django group for the user."""

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    email = models.EmailField("email address", blank=True)
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=ROLE_WORKER, db_index=True
    )
    phone = models.CharField(max_length=32, blank=True)
    # Farms a (worker/manager) user is explicitly assigned to. Owners use the
    # Farm.owner relation; admins see all farms.
    assigned_farms = models.ManyToManyField(
        "farms.Farm", blank=True, related_name="assigned_users"
    )

    objects = CustomUserManager()

    class Meta:
        ordering = ["username"]

    def __str__(self):
        full = self.get_full_name()
        return f"{full} ({self.username})" if full else self.username

    # -- role helpers -----------------------------------------------------
    def sync_primary_group(self):
        """Ensure the user belongs to the group matching ``self.role``."""
        group, _ = Group.objects.get_or_create(name=self.role)
        if not self.groups.filter(name=self.role).exists():
            self.groups.add(group)

    def has_role(self, role: str) -> bool:
        if self.is_superuser and role == "ADMIN":
            return True
        return self.role == role or self.groups.filter(name=role).exists()

    def has_any_role(self, roles) -> bool:
        return any(self.has_role(r) for r in roles)

    def has_capability(self, capability: str) -> bool:
        if self.is_superuser:
            return True
        role_names = list(self.groups.values_list("name", flat=True))
        if self.role not in role_names:
            role_names.append(self.role)
        return any(role_has_capability(r, capability) for r in role_names)

    @property
    def role_label(self):
        return self.get_role_display()


class UserProfile(models.Model):
    """Extended profile information kept separate from auth fields."""

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    job_title = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    timezone = models.CharField(max_length=64, default="Africa/Douala")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user}"
