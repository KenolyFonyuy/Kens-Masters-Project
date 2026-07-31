"""Shared pytest fixtures."""
import pytest
from apps.accounts.models import CustomUser
from apps.farms.models import Farm, Pen
from apps.flocks.models import Batch, ChickEntry
from apps.iot.models import DeviceToken, IoTDevice
from django.core.management import call_command


@pytest.fixture(autouse=True)
def _roles(db):
    """Ensure role groups exist for permission tests."""
    call_command("setup_roles")


@pytest.fixture
def owner(db):
    u = CustomUser.objects.create_user("owner1", password="pw", role="OWNER")
    return u


@pytest.fixture
def manager(db):
    return CustomUser.objects.create_user("mgr1", password="pw", role="MANAGER")


@pytest.fixture
def worker(db):
    return CustomUser.objects.create_user("wkr1", password="pw", role="WORKER")


@pytest.fixture
def vet(db):
    return CustomUser.objects.create_user("vet1", password="pw", role="VET")


@pytest.fixture
def farm(db, owner):
    return Farm.objects.create(name="Test Farm", code="TST1", owner=owner)


@pytest.fixture
def other_farm(db):
    return Farm.objects.create(name="Other Farm", code="OTH1")


@pytest.fixture
def pen(db, farm):
    return Pen.objects.create(farm=farm, name="Pen 1", code="P1", capacity=500)


@pytest.fixture
def batch(db, farm, pen):
    b = Batch.objects.create(farm=farm, pen=pen, code="B1", status=Batch.Status.ACTIVE)
    ChickEntry.objects.create(batch=b, quantity=500)
    return b


@pytest.fixture
def device(db, farm, pen):
    return IoTDevice.objects.create(device_id="PI-TEST", name="Pi", farm=farm, pen=pen)


@pytest.fixture
def device_token(db, device):
    token, raw = DeviceToken.issue(device)
    return raw


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()
