"""Transactional stock operations with row locking."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import InventoryItem, StockMovement


@transaction.atomic
def apply_movement(item, *, movement_type, quantity, allow_negative=False, **fields):
    """Create a stock movement, validating non-negative stock under a row lock."""
    locked = InventoryItem.objects.select_for_update().get(pk=item.pk)
    quantity = Decimal(str(quantity))
    is_positive = movement_type in StockMovement.POSITIVE
    if not is_positive and not allow_negative:
        projected = locked.current_stock - quantity
        if projected < 0:
            raise ValidationError(
                f"Insufficient stock for {locked.name}: have {locked.current_stock}, "
                f"need {quantity}."
            )
    return StockMovement.objects.create(
        item=locked,
        movement_type=movement_type,
        quantity=quantity,
        allow_negative=allow_negative,
        **fields,
    )


def issue_for_feed_usage(feed_usage):
    """Decrement the linked inventory item when feed is used (idempotent)."""
    feed_type = feed_usage.feed_type
    if feed_usage.stock_applied or not feed_type or not feed_type.inventory_item_id:
        return None
    movement = apply_movement(
        feed_type.inventory_item,
        movement_type=StockMovement.Type.ISSUE,
        quantity=feed_usage.quantity_kg,
        allow_negative=True,  # do not block recording field reality
        reference=f"FeedUsage:{feed_usage.uid}",
        notes=f"Auto feed usage for batch {feed_usage.batch.code}",
        movement_date=feed_usage.record_date,
    )
    feed_usage.stock_applied = True
    feed_usage.save(update_fields=["stock_applied"])
    return movement
