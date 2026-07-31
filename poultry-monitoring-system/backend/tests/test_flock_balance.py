"""Flock-balance and transaction-validation tests."""
import pytest
from apps.finance.models import Sale
from apps.flocks.models import MortalityRecord
from apps.flocks.services import record_mortality, record_transfer
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


def test_initial_balance_equals_entries(batch):
    assert batch.total_entries == 500
    assert batch.current_quantity == 500


def test_mortality_reduces_balance(batch):
    MortalityRecord.objects.create(batch=batch, quantity=10)
    assert batch.current_quantity == 490


def test_mortality_cannot_exceed_flock(batch):
    with pytest.raises(ValidationError):
        record_mortality(batch, quantity=600)


def test_service_mortality_ok(batch):
    record_mortality(batch, quantity=20)
    assert batch.current_quantity == 480


def test_confirmed_sale_reduces_balance(batch):
    Sale.objects.create(
        farm=batch.farm, batch=batch, quantity=100, unit_price=3000,
        status=Sale.Status.CONFIRMED,
    )
    assert batch.current_quantity == 400
    assert batch.total_sold == 100


def test_draft_sale_does_not_reduce_balance(batch):
    Sale.objects.create(
        farm=batch.farm, batch=batch, quantity=100, unit_price=3000,
        status=Sale.Status.DRAFT,
    )
    assert batch.current_quantity == 500


def test_sale_validation_rejects_oversell(batch):
    sale = Sale(
        farm=batch.farm, batch=batch, quantity=600, unit_price=3000,
        status=Sale.Status.CONFIRMED,
    )
    with pytest.raises(ValidationError):
        sale.full_clean()


def test_transfer_validation_and_balance(batch, farm):
    from apps.flocks.models import Batch

    dest = Batch.objects.create(farm=farm, code="B2", status=Batch.Status.ACTIVE)
    record_transfer(batch, quantity=50, destination_batch=dest)
    assert batch.current_quantity == 450
    assert dest.current_quantity == 50  # transfer in


def test_transfer_cannot_exceed_flock(batch):
    with pytest.raises(ValidationError):
        record_transfer(batch, quantity=9999)


def test_mortality_model_clean_blocks_oversell(batch):
    rec = MortalityRecord(batch=batch, quantity=10_000)
    with pytest.raises(ValidationError):
        rec.full_clean()


def test_cumulative_mortality_rate(batch):
    MortalityRecord.objects.create(batch=batch, quantity=25)
    assert batch.cumulative_mortality_rate == pytest.approx(5.0)
