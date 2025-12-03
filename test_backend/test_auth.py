import pytest
from flask import Flask, g, request
from unittest.mock import MagicMock
from backend.auth import keycloak_protect

# Tests the decorator when the Authorization header is completely missing.
def test_keycloak_protect_missing_header():
    app = Flask(__name__)

    @app.route("/secure")
    @keycloak_protect
    def secure():
        return "ok", 200

    client = app.test_client()
    response = client.get("/secure")  # no Header
    assert response.status_code == 401
    assert "Missing" in response.get_json()["error"]

# Tests the decorator when the Authorization header has an invalid format.
def test_keycloak_protect_invalid_format_header():
    app = Flask(__name__)

    @app.route("/secure")
    @keycloak_protect
    def secure():
        return "ok", 200

    client = app.test_client()
    # Test with a header that does not start with "Bearer "
    response = client.get("/secure", headers={"Authorization": "Token invalid"})
    assert response.status_code == 401
    assert "Missing or invalid Authorization header" in response.get_json()["error"]


# Tests the decorator when an invalid/unverified token is provided.
def test_keycloak_protect_invalid_header(monkeypatch):
    app = Flask(__name__)

    # Mock KeycloakOpenID.userinfo to simulate a token validation failure
    from backend import auth
    monkeypatch.setattr(auth.keycloak_openid, "userinfo", lambda token: (_ for _ in ()).throw(Exception("invalid")))

    @app.route("/secure")
    @auth.keycloak_protect
    def secure():
        return "ok", 200

    client = app.test_client()
    response = client.get("/secure", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert "Token invalid" in response.get_json()["error"]

# Tests the decorator with a valid token.
def test_keycloak_protect_valid_token(monkeypatch):
    app = Flask(__name__)
    user_info = {"sub": "123", "name": "test user"}

    # Mock KeycloakOpenID.userinfo to simulate a successful token validation
    from backend import auth
    monkeypatch.setattr(auth.keycloak_openid, "userinfo", lambda token: user_info)

    @app.route("/secure")
    @auth.keycloak_protect
    def secure():
        # Assert that g.user and request.user are set correctly
        assert g.user == user_info
        assert request.user == user_info
        return "ok", 200

    client = app.test_client()
    response = client.get("/secure", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 200
    assert response.data == b"ok"

# Tests the decorator when the access token is expired and the refresh token is also invalid.
def test_keycloak_protect_expired_token_invalid_refresh(monkeypatch):
    app = Flask(__name__)

    # Mock KeycloakOpenID methods
    from backend import auth
    # 1. userinfo fails, simulating an expired token
    monkeypatch.setattr(auth.keycloak_openid, "userinfo", MagicMock(side_effect=Exception("expired")))
    # 2. refresh_token also fails, simulating an invalid refresh token
    monkeypatch.setattr(auth.keycloak_openid, "refresh_token", MagicMock(side_effect=Exception("invalid refresh")))

    @app.route("/secure")
    @auth.keycloak_protect
    def secure():
        return "ok", 200

    client = app.test_client()
    response = client.get("/secure", headers={
        "Authorization": "Bearer expired-token",
        "X-Refresh-Token": "invalid-refresh-token"
    })
    assert response.status_code == 401
    assert "Token invalid or expired" in response.get_json()["error"]
    assert "invalid refresh" in response.get_json()["details"]

# Tests the decorator when the access token is expired but the refresh is successful.
def test_keycloak_protect_expired_token_successful_refresh(monkeypatch):
    app = Flask(__name__)
    new_tokens = {"access_token": "new-valid-token"}
    user_info = {"sub": "123", "name": "refreshed user"}

    # Mock KeycloakOpenID methods
    from backend import auth
    mock_userinfo = MagicMock()
    # 1. First call to userinfo fails (expired token)
    # 2. Second call succeeds with the new token
    mock_userinfo.side_effect = [Exception("expired"), user_info]
    monkeypatch.setattr(auth.keycloak_openid, "userinfo", mock_userinfo)
    # The refresh_token call succeeds and returns new tokens
    monkeypatch.setattr(auth.keycloak_openid, "refresh_token", lambda refresh_token: new_tokens)

    @app.route("/secure")
    @auth.keycloak_protect
    def secure():
        assert g.user == user_info
        assert g.access_token == "new-valid-token"
        return "ok", 200

    client = app.test_client()
    response = client.get("/secure", headers={
        "Authorization": "Bearer expired-token",
        "X-Refresh-Token": "valid-refresh-token"
    })
    assert response.status_code == 200
    assert response.data == b"ok"
