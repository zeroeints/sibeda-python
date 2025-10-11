from __future__ import annotations
from fastapi.testclient import TestClient
from typing import Dict, Any

# Helper payload
USER_PAYLOAD: Dict[str, Any] = {
    # 18 chars NIP
    "NIP": "123456789012345678",
    "NamaLengkap": "Tester Satu",
    "Email": "tester@example.com",
    "NoTelepon": "08123456789",
    "Password": "secretpass"
}

def test_register_user_success(client: TestClient):
    resp = client.post("/users/register", json=USER_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["NIP"] == USER_PAYLOAD["NIP"]
    assert "ID" in body["data"]
    assert body["data"].get("isVerified") in (False, None)

def test_register_user_duplicate(client: TestClient):
    client.post("/users/register", json=USER_PAYLOAD)
    resp = client.post("/users/register", json=USER_PAYLOAD)
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == 400
    assert body["message"] == "NIP atau Email sudah terdaftar"


def test_register_user_nip_too_short(client: TestClient):
    payload = USER_PAYLOAD.copy()
    payload["Email"] = "shortnip@example.com"
    payload["NIP"] = "123"  # too short
    resp = client.post("/users/register", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    # pydantic v2 error structure
    assert any(err["loc"][-1] == "NIP" for err in body["detail"])  # type: ignore


def test_register_user_password_too_short(client: TestClient):
    payload = USER_PAYLOAD.copy()
    payload["Email"] = "shortpwd@example.com"
    payload["NIP"] = "999999999999999999"  # ensure unique & valid length
    payload["Password"] = "123"  # too short
    resp = client.post("/users/register", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert any(err["loc"][-1] == "Password" for err in body["detail"])  # type: ignore

def test_login_and_token_claims(client: TestClient):
    # ensure user exists
    client.post("/users/register", json=USER_PAYLOAD)
    # login (username == NIP per authenticate_user usage)
    resp = client.post("/login", data={"username": USER_PAYLOAD["NIP"], "password": USER_PAYLOAD["Password"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    token = body["data"]["access_token"]
    assert token
    # Basic structure check of JWT (three parts)
    assert token.count('.') == 2
