import pytest


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_standard_user(self, api_client):
        resp = api_client.post(
            "/api/auth/register/",
            {"username": "newuser", "email": "n@test.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["username"] == "newuser"
        assert "password" not in body

    def test_register_rejects_weak_password(self, api_client):
        resp = api_client.post(
            "/api/auth/register/",
            {"username": "weakpw", "email": "w@test.com", "password": "12345678"},
        )
        assert resp.status_code == 400

    def test_register_rejects_duplicate_username(self, api_client, standard_user):
        resp = api_client.post(
            "/api/auth/register/",
            {
                "username": standard_user.username,
                "email": "dupe@test.com",
                "password": "StrongPass123!",
            },
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestTokenAuth:
    def test_obtain_token_with_valid_credentials(self, api_client, standard_user):
        resp = api_client.post(
            "/api/auth/token/",
            {"username": standard_user.username, "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        assert "access" in resp.json()
        assert "refresh" in resp.json()

    def test_refresh_token(self, api_client, standard_user):
        obtain = api_client.post(
            "/api/auth/token/",
            {"username": standard_user.username, "password": "StrongPass123!"},
        )
        refresh_token = obtain.json()["refresh"]
        resp = api_client.post("/api/auth/token/refresh/", {"refresh": refresh_token})
        assert resp.status_code == 200
        assert "access" in resp.json()


@pytest.mark.django_db
class TestMe:
    def test_me_requires_authentication(self, api_client):
        resp = api_client.get("/api/auth/me/")
        assert resp.status_code == 401

    def test_me_returns_current_user_and_role(self, standard_client, standard_user):
        resp = standard_client.get("/api/auth/me/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == standard_user.username
        assert body["role"] == "STANDARD"
