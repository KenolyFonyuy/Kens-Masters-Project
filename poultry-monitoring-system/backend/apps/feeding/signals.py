"""Auto-decrement linked inventory when feed usage is recorded."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FeedUsage


@receiver(post_save, sender=FeedUsage)
def decrement_feed_inventory(sender, instance, created, **kwargs):
    if not created:
        return
    from apps.inventory.services import issue_for_feed_usage

    try:
        issue_for_feed_usage(instance)
    except Exception:  # pragma: no cover - never block recording field reality
        pass
