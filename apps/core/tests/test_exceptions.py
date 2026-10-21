from unittest import mock

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestStandardizedErrorShape:
    def test_validation_error_has_standard_shape(self, admin_client):
        resp = admin_client.post(
            "/api/products/", {"sku": "bad sku!", "name": "X", "unit_price": "-5"}
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["error"]["code"] == "invalid"
        assert "sku" in body["error"]["details"]
        assert "unit_price" in body["error"]["details"]

    def test_authentication_failure_has_standard_shape(self, api_client):
        resp = api_client.post("/api/auth/token/", {"username": "nobody", "password": "wrong"})
        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["code"] == "authentication_failed"
        assert "message" in body["error"]

    def test_unauthenticated_request_is_401_standard_shape(self, api_client):
        resp = api_client.get("/api/suppliers/")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "not_authenticated"

    def test_permission_denied_is_403_standard_shape(self, standard_client, supplier):
        resp = standard_client.delete(f"/api/suppliers/{supplier.id}/")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "permission_denied"

    def test_missing_resource_is_404_with_not_found_code(self, admin_client):
        resp = admin_client.get("/api/products/999999/")
        assert resp.status_code == 404
        # Regression check: this used to read "Http404" instead of DRF's
        # normal "not_found" because the exc wasn't converted before the
        # default_code lookup.
        assert resp.json()["error"]["code"] == "not_found"

    def test_protected_delete_returns_409_not_500(self, admin_client, product, warehouse):
        admin_client.post(
            "/api/stock-movements/",
            {
                "product": product.id,
                "warehouse": warehouse.id,
                "movement_type": "RECEIPT",
                "quantity": 10,
            },
        )
        resp = admin_client.delete(f"/api/warehouses/{warehouse.id}/")
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "conflict"


@pytest.mark.django_db
class TestSiteWideErrorHandlers:
    """handler404/handler500 only kick in under DEBUG=False."""

    def test_unmatched_api_url_returns_json_404(self, settings):
        settings.DEBUG = False
        settings.ALLOWED_HOSTS = ["testserver"]
        resp = APIClient().get("/api/this-route-does-not-exist/")
        assert resp.status_code == 404
        assert resp["Content-Type"] == "application/json"
        assert resp.json()["error"]["code"] == "not_found"

    def test_unmatched_non_api_url_stays_html(self, settings):
        settings.DEBUG = False
        settings.ALLOWED_HOSTS = ["testserver"]
        resp = APIClient().get("/this-is-not-a-real-page/")
        assert resp.status_code == 404
        assert "text/html" in resp["Content-Type"]

    def test_unhandled_exception_returns_json_500(self, settings):
        settings.DEBUG = False
        settings.ALLOWED_HOSTS = ["testserver"]
        client = APIClient(raise_request_exception=False)
        with mock.patch(
            "apps.accounts.serializers.RegisterSerializer.create",
            side_effect=Exception("simulated outage"),
        ):
            resp = client.post(
                "/api/auth/register/",
                {"username": "crashtest", "email": "c@test.com", "password": "StrongPass123!"},
            )
        assert resp.status_code == 500
        assert resp.json()["error"]["code"] == "server_error"
