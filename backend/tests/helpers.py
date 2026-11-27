"""Small API helpers shared by the Fase 2 test modules."""

from decimal import Decimal

from fastapi.testclient import TestClient

API = "/api/v1"
PASSWORD = "ValidPass123!"


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    client.post(f"{API}/auth/register", json={"email": email, "password": PASSWORD})
    login = client.post(f"{API}/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def make_account(client: TestClient, headers: dict, name: str, bucket: str, balance: str = "0.00") -> dict:
    r = client.post(f"{API}/accounts", json={"name": name, "bucket_type": bucket, "initial_balance": balance}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def make_category(client: TestClient, headers: dict, name: str, ctype: str, is_fixed: bool = False) -> dict:
    r = client.post(f"{API}/categories", json={"name": name, "type": ctype, "is_fixed": is_fixed}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def balance(client: TestClient, headers: dict, account_id: int) -> Decimal:
    return Decimal(str(client.get(f"{API}/accounts/{account_id}", headers=headers).json()["current_balance"]))


def make_fund(client: TestClient, headers: dict, account_id: int, isin: str = "IE00B4L5Y983", nav: str = "0") -> dict:
    r = client.post(
        f"{API}/funds",
        json={"account_id": account_id, "isin": isin, "fund_name": "MSCI World", "current_nav": nav},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def contribute(client: TestClient, headers: dict, fund_id: int, **fields):
    body = {"operation_date": "2026-01-15", "order_type": "buy", "fee": "0.00", **fields}
    return client.post(f"{API}/funds/{fund_id}/contributions", json=body, headers=headers)
