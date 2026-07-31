"""Transactional flock-balance operations with row locking.

These helpers are the safe path for mutating flock quantities. They lock the
batch row (``select_for_update``) so concurrent mortality/transfer/sale entries
cannot race past the available-bird check. ``ValidationError`` is raised when a
rule would be violated; nothing is silently dropped.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Batch, MortalityRecord, TransferRecord


@transaction.atomic
def record_mortality(batch, *, quantity, **fields):
    locked = Batch.objects.select_for_update().get(pk=batch.pk)
    available = locked.current_quantity
    if quantity > available:
        raise ValidationError(
            f"Mortality ({quantity}) exceeds the live flock ({available})."
        )
    return MortalityRecord.objects.create(batch=locked, quantity=quantity, **fields)


@transaction.atomic
def record_transfer(source_batch, *, quantity, **fields):
    locked = Batch.objects.select_for_update().get(pk=source_batch.pk)
    available = locked.current_quantity
    if quantity > available:
        raise ValidationError(
            f"Transfer ({quantity}) exceeds the live flock ({available})."
        )
    return TransferRecord.objects.create(source_batch=locked, quantity=quantity, **fields)


def available_birds(batch) -> int:
    """Convenience wrapper for the live bird count."""
    return Batch.objects.get(pk=batch.pk).current_quantity
