"""Audit logging and generic file attachments."""
import uuid

from apps.core.models import TimeStampedModel
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


def attachment_upload_path(instance, filename):
    return f"attachments/{instance.uid}/{filename}"


class AuditLog(models.Model):
    """Immutable record of significant actions (login, create, update, etc.)."""

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        LOGIN_FAILED = "login_failed", "Login failed"
        EXPORT = "export", "Export"
        API = "api", "API action"
        ALERT = "alert", "Alert action"

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    target_repr = models.CharField(max_length=255, blank=True)
    object_type = models.CharField(max_length=120, blank=True, db_index=True)
    object_id = models.CharField(max_length=64, blank=True)
    message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["action", "timestamp"])]

    def __str__(self):
        who = self.user or "system"
        return f"{self.timestamp:%Y-%m-%d %H:%M} {who} {self.action} {self.target_repr}"


class Attachment(TimeStampedModel):
    """Generic file attachment that can be linked to any record."""

    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file = models.FileField(upload_to=attachment_upload_path)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.CharField(max_length=64, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="attachments",
    )

    def __str__(self):
        return self.original_name or self.file.name
