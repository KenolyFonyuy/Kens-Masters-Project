"""Transactional confirmed-sale creation with flock row locking."""
from apps.flocks.models import Batch
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Sale


@transaction.atomic
def create_confirmed_sale(batch, *, quantity, unit_price, **fields):
    locked = Batch.objects.select_for_update().get(pk=batch.pk)
    available = locked.current_quantity
    if quantity > available:
        raise ValidationError(
            f"Sale ({quantity}) exceeds the live flock ({available})."
        )
    return Sale.objects.create(
        farm=locked.farm,
        batch=locked,
        quantity=quantity,
        unit_price=unit_price,
        status=Sale.Status.CONFIRMED,
        **fields,
    )
