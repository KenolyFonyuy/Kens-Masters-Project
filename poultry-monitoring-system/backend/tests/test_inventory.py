"""Inventory balance and feed-usage auto-decrement tests."""
import pytest
from apps.feeding.models import FeedType, FeedUsage
from apps.inventory.models import InventoryItem, StockMovement
from apps.inventory.services import apply_movement
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


@pytest.fixture
def item(farm):
    return InventoryItem.objects.create(
        farm=farm, name="Feed A", unit="kg", opening_stock=100, reorder_level=20
    )


def test_opening_stock_is_balance(item):
    assert item.current_stock == 100


def test_receipt_increases_stock(item):
    StockMovement.objects.create(item=item, movement_type=StockMovement.Type.RECEIPT, quantity=50)
    assert item.current_stock == 150


def test_issue_decreases_stock(item):
    StockMovement.objects.create(item=item, movement_type=StockMovement.Type.ISSUE, quantity=30)
    assert item.current_stock == 70


def test_issue_cannot_go_negative_without_override(item):
    with pytest.raises(ValidationError):
        apply_movement(item, movement_type=StockMovement.Type.ISSUE, quantity=500)


def test_privileged_negative_override(item):
    apply_movement(item, movement_type=StockMovement.Type.ISSUE, quantity=500, allow_negative=True)
    assert item.current_stock == -400


def test_low_stock_flag(item):
    StockMovement.objects.create(item=item, movement_type=StockMovement.Type.ISSUE, quantity=85)
    assert item.current_stock == 15
    assert item.is_low_stock is True


def test_feed_usage_decrements_inventory(batch, item):
    feed_type = FeedType.objects.create(name="Starter", inventory_item=item)
    FeedUsage.objects.create(batch=batch, feed_type=feed_type, quantity_kg=40)
    item.refresh_from_db()
    assert item.current_stock == 60


def test_signed_quantity_is_set(item):
    m = StockMovement.objects.create(item=item, movement_type=StockMovement.Type.EXPIRY, quantity=10)
    assert m.signed_quantity == -10
