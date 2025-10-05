from __future__ import annotations
from fastapi.testclient import TestClient
from typing import Dict, Any

# Helper payload
USER_PAYLOAD: Dict[str, Any] = {
    "NIP": "123456789",
    "NamaLengkap": "Tester Satu",
    "Email": "tester@example.com",
    "NoTelepon": "08123456789",
    "Password": "secretpass",
    "DinasID": None
}

def test_create_user_success(client: TestClient):
    resp = client.post("/users/", json=USER_PAYLOAD)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["NIP"] == USER_PAYLOAD["NIP"]
    assert "ID" in body["data"]

def test_create_user_duplicate(client: TestClient):
    client.post("/users/", json=USER_PAYLOAD)
    resp = client.post("/users/", json=USER_PAYLOAD)
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == 400
    assert body["message"] == "NIP atau Email sudah terdaftar"

def test_login_and_token_claims(client: TestClient):
    # ensure user exists
    client.post("/users/", json=USER_PAYLOAD)
    # login (username == NIP per authenticate_user usage)
    resp = client.post("/login", data={"username": USER_PAYLOAD["NIP"], "password": USER_PAYLOAD["Password"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    token = body["data"]["access_token"]
    assert token
    # Basic structure check of JWT (three parts)
    assert token.count('.') == 2
