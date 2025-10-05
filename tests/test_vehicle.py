from __future__ import annotations
from fastapi.testclient import TestClient
from typing import Dict, Any

VEHICLE_TYPE_PAYLOAD = {"Nama": "Mobil"}
USER_PAYLOAD: Dict[str, Any] = {
    "NIP": "vehuser1",
    "NamaLengkap": "Vehicle User",
    "Email": "vehuser@example.com",
    "NoTelepon": "0800000000",
    "Password": "secretpass",
    "DinasID": None
}

VEHICLE_BASE: Dict[str, Any] = {
    "Nama": "Avanza 1",
    "Plat": "B1234CD",
    "VehicleTypeID": 1,
    "KapasitasMesin": 1500,
    "Odometer": 1000,
    "Status": "Active",
    "JenisBensin": "Pertalite",
    "Merek": "Toyota",
    "FotoFisik": None
}

def ensure_prereqs(client: TestClient):
    # create vehicle type id=1
    client.post("/wallet/types", json={"Nama": "DummyWalletType"})  # not needed but safe
    client.post("/users/", json=USER_PAYLOAD)
    # create a vehicle type (not previously implemented route? If absent we skip)
    # If there is no route for vehicle type creation, tests depending on VehicleTypeID=1 assume seed.


def test_vehicle_create_success(client: TestClient):
    ensure_prereqs(client)
    resp = client.post("/vehicle/", json=VEHICLE_BASE)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["Plat"] == VEHICLE_BASE["Plat"]


def test_vehicle_duplicate_plat(client: TestClient):
    ensure_prereqs(client)
    client.post("/vehicle/", json=VEHICLE_BASE)
    resp = client.post("/vehicle/", json=VEHICLE_BASE)
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == 400
    assert body["message"] == "Plat sudah terdaftar"


def test_vehicle_invalid_vehicle_type(client: TestClient):
    ensure_prereqs(client)
    bad_payload: Dict[str, Any] = {**VEHICLE_BASE, "Plat": "B9999ZZ", "VehicleTypeID": 9999}
    resp = client.post("/vehicle/", json=bad_payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == 400
    assert body["message"] == "VehicleTypeID tidak ditemukan"
