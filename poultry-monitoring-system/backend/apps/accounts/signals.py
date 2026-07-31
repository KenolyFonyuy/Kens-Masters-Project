"""Keep a UserProfile and primary group in sync with each user."""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def ensure_profile_and_group(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
    # Mirror the primary role into Django groups.
    instance.sync_primary_group()


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    from apps.audit.models import AuditLog
    from apps.audit.services import log_action

    log_action(AuditLog.Action.LOGIN, target=user, message="User logged in", request=request)


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request=None, **kwargs):
    from apps.audit.models import AuditLog
    from apps.audit.services import log_action

    username = credentials.get("username", "?")
    log_action(
        AuditLog.Action.LOGIN_FAILED,
        message=f"Failed login for '{username}'",
        request=request,
    )
