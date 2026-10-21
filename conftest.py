import pytest
from rest_framework.test import APIClient

from apps.inventory.models import Product, Supplier, Warehouse


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def standard_user(django_user_model):
    return django_user_model.objects.create_user("standard", password="StrongPass123!")


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_user("admin", password="StrongPass123!", is_staff=True)


@pytest.fixture
def standard_client(api_client, standard_user):
    api_client.force_authenticate(user=standard_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(name="Acme Co", contact_email="a@acme.test")


@pytest.fixture
def warehouse(db):
    return Warehouse.objects.create(code="SEA1", name="Seattle DC")


@pytest.fixture
def product(db):
    return Product.objects.create(sku="WIDGET-001", name="Widget", unit_price="9.99")
