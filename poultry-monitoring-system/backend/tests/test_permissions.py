"""Role permission and farm data-isolation tests."""
import pytest
from apps.farms.services import farms_for_user, user_can_access_farm
from django.test import Client

pytestmark = pytest.mark.django_db


def test_owner_sees_only_owned_farm(owner, farm, other_farm):
    farms = farms_for_user(owner)
    assert farm in farms
    assert other_farm not in farms


def test_admin_sees_all_farms(db, farm, other_farm):
    from apps.accounts.models import CustomUser

    admin = CustomUser.objects.create_user("admin1", password="pw", role="ADMIN")
    farms = farms_for_user(admin)
    assert farm in farms and other_farm in farms


def test_worker_only_assigned_farm(worker, farm, other_farm):
    worker.assigned_farms.add(farm)
    assert user_can_access_farm(worker, farm) is True
    assert user_can_access_farm(worker, other_farm) is False


def test_login_required_redirect():
    c = Client()
    resp = c.get("/farms/")
    assert resp.status_code == 302
    assert "/accounts/login/" in resp.url


def test_worker_cannot_open_finance(worker, farm):
    worker.assigned_farms.add(farm)
    c = Client()
    c.force_login(worker)
    resp = c.get("/finance/expenses/")
    assert resp.status_code == 403


def test_manager_can_open_finance(manager, farm):
    manager.assigned_farms.add(farm)
    c = Client()
    c.force_login(manager)
    resp = c.get("/finance/expenses/")
    assert resp.status_code == 200


def test_worker_cannot_create_farm(worker):
    c = Client()
    c.force_login(worker)
    resp = c.get("/farms/add/")
    assert resp.status_code == 403


def test_dashboard_loads_for_authenticated(manager, farm):
    manager.assigned_farms.add(farm)
    c = Client()
    c.force_login(manager)
    resp = c.get("/")
    assert resp.status_code == 200


def test_farm_list_isolation_in_view(owner, manager, farm, other_farm):
    """A manager assigned to other_farm must not see owner's farm in the list."""
    manager.assigned_farms.add(other_farm)
    c = Client()
    c.force_login(manager)
    resp = c.get("/farms/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "Other Farm" in content
    assert "Test Farm" not in content
