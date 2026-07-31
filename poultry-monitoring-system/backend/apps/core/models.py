"""Abstract base models shared across the whole project.

Every important record gets:
  * a stable UUID identifier (``uid``) safe to expose in URLs/APIs,
  * created/updated timestamps,
  * created_by / updated_by audit columns.

``created_by`` / ``updated_by`` are populated automatically by the
``TimeStampedUserModel.save`` helper in cooperation with
``apps.audit.middleware.CurrentUserMiddleware``.
"""
import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    """Adds a stable, indexed UUID field (kept separate from the PK)."""

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = "created_at"


class TimeStampedUserModel(UUIDModel, TimeStampedModel):
    """Base for domain records: UUID + timestamps + created/updated user."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from apps.audit.middleware import get_current_user

        user = get_current_user()
        if user is not None and getattr(user, "is_authenticated", False):
            if self._state.adding and self.created_by_id is None:
                self.created_by = user
            self.updated_by = user
        super().save(*args, **kwargs)
