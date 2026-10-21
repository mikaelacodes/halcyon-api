from unittest import mock

import pytest
from django.db import OperationalError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_ok_when_db_is_up():
    resp = APIClient().get("/health/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"]["connected"] is True
    assert body["uptime_seconds"] >= 0


@pytest.mark.django_db
def test_health_check_requires_no_auth():
    # No force_authenticate, no token header - should still work.
    resp = APIClient().get("/health/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_health_check_reports_503_when_db_is_down():
    with mock.patch(
        "django.db.backends.utils.CursorWrapper.execute",
        side_effect=OperationalError("could not connect"),
    ):
        resp = APIClient().get("/health/")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "unhealthy"
    assert body["database"]["connected"] is False
