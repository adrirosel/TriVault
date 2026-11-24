"""Transaction atomicity, balance invariants, IDOR, and cross-account transfer tests."""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, email: str) -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": "ValidPass123!"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "ValidPass123!"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _make_account(client: TestClient, headers: dict, name: str, bucket: str, balance: str = "1000.00") -> dict:
    r = client.post(
        "/api/v1/accounts",
        json={"name": name, "bucket_type": bucket, "initial_balance": balance},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


def _make_category(client: TestClient, headers: dict, name: str, ctype: str) -> dict:
    r = client.post("/api/v1/categories", json={"name": name, "type": ctype}, headers=headers)
    assert r.status_code == 201
    return r.json()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_income_and_expense_update_balances_atomically(client: TestClient) -> None:
    """Income increases balance; expense decreases it; both are reflected immediately."""
    h = _auth_headers(client, "txbalance@example.com")
    acc = _make_account(client, h, "Corriente", "daily", "500.00")
    cat_inc = _make_category(client, h, "Salario", "income")
    cat_exp = _make_category(client, h, "Comida", "expense")

    # Income +200
    r_inc = client.post("/api/v1/transactions", json={
        "account_id": acc["id"], "amount": "200.00", "type": "income",
        "category_id": cat_inc["id"], "transaction_date": _now_iso(),
    }, headers=h)
    assert r_inc.status_code == 201
    acc_after_inc = client.get(f"/api/v1/accounts/{acc['id']}", headers=h).json()
    assert Decimal(str(acc_after_inc["current_balance"])) == Decimal("700.00")

    # Expense -100
    r_exp = client.post("/api/v1/transactions", json={
        "account_id": acc["id"], "amount": "100.00", "type": "expense",
        "category_id": cat_exp["id"], "transaction_date": _now_iso(),
    }, headers=h)
    assert r_exp.status_code == 201
    acc_after_exp = client.get(f"/api/v1/accounts/{acc['id']}", headers=h).json()
    assert Decimal(str(acc_after_exp["current_balance"])) == Decimal("600.00")


def test_transfer_updates_both_balances_atomically(client: TestClient) -> None:
    """Transfer deducts from source and credits destination in the same commit."""
    h = _auth_headers(client, "txtransfer@example.com")
    src = _make_account(client, h, "Diaria", "daily", "800.00")
    dst = _make_account(client, h, "Emergencia", "emergency", "200.00")

    r = client.post("/api/v1/transactions", json={
        "account_id": src["id"],
        "amount": "300.00",
        "type": "transfer",
        "destination_account_id": dst["id"],
        "transaction_date": _now_iso(),
    }, headers=h)
    assert r.status_code == 201

    src_after = client.get(f"/api/v1/accounts/{src['id']}", headers=h).json()
    dst_after = client.get(f"/api/v1/accounts/{dst['id']}", headers=h).json()
    assert Decimal(str(src_after["current_balance"])) == Decimal("500.00")
    assert Decimal(str(dst_after["current_balance"])) == Decimal("500.00")


def test_delete_transaction_reverses_balance(client: TestClient) -> None:
    """Deleting a transaction atomically reverses its balance impact."""
    h = _auth_headers(client, "txdelete@example.com")
    acc = _make_account(client, h, "Ahorro", "emergency", "1000.00")
    cat = _make_category(client, h, "Extra", "income")

    tx = client.post("/api/v1/transactions", json={
        "account_id": acc["id"], "amount": "250.00", "type": "income",
        "category_id": cat["id"], "transaction_date": _now_iso(),
    }, headers=h).json()
    assert Decimal(str(client.get(f"/api/v1/accounts/{acc['id']}", headers=h).json()["current_balance"])) == Decimal("1250.00")

    del_r = client.delete(f"/api/v1/transactions/{tx['id']}", headers=h)
    assert del_r.status_code == 204
    assert Decimal(str(client.get(f"/api/v1/accounts/{acc['id']}", headers=h).json()["current_balance"])) == Decimal("1000.00")


def test_transfer_validation_rejects_same_account_and_missing_destination(client: TestClient) -> None:
    """Schema validation blocks self-transfers and transfers without destination."""
    h = _auth_headers(client, "txvalidation@example.com")
    acc = _make_account(client, h, "Única", "daily", "500.00")

    same = client.post("/api/v1/transactions", json={
        "account_id": acc["id"], "amount": "100.00", "type": "transfer",
        "destination_account_id": acc["id"], "transaction_date": _now_iso(),
    }, headers=h)
    assert same.status_code == 422

    no_dest = client.post("/api/v1/transactions", json={
        "account_id": acc["id"], "amount": "100.00", "type": "transfer",
        "transaction_date": _now_iso(),
    }, headers=h)
    assert no_dest.status_code == 422

    income_with_dest = client.post("/api/v1/transactions", json={
        "account_id": acc["id"], "amount": "100.00", "type": "income",
        "category_id": 999, "destination_account_id": acc["id"],
        "transaction_date": _now_iso(),
    }, headers=h)
    assert income_with_dest.status_code == 422


def test_transaction_idor_cross_user(client: TestClient) -> None:
    """User B cannot read or delete User A's transactions."""
    h_a = _auth_headers(client, "txidora@example.com")
    h_b = _auth_headers(client, "txidorb@example.com")

    acc_a = _make_account(client, h_a, "Cuenta A", "daily", "500.00")
    cat_a = _make_category(client, h_a, "Misc", "expense")

    tx_a = client.post("/api/v1/transactions", json={
        "account_id": acc_a["id"], "amount": "50.00", "type": "expense",
        "category_id": cat_a["id"], "transaction_date": _now_iso(),
    }, headers=h_a).json()

    assert client.get(f"/api/v1/transactions/{tx_a['id']}", headers=h_b).status_code == 404
    assert client.delete(f"/api/v1/transactions/{tx_a['id']}", headers=h_b).status_code == 404
    # Account A balance must be unchanged
    acc_check = client.get(f"/api/v1/accounts/{acc_a['id']}", headers=h_a).json()
    assert Decimal(str(acc_check["current_balance"])) == Decimal("450.00")


def test_transfer_using_foreign_destination_account_returns_404(client: TestClient) -> None:
    """Cannot transfer to another user's account; service returns 404."""
    h_a = _auth_headers(client, "txforeignsrc@example.com")
    h_b = _auth_headers(client, "txforeigndst@example.com")

    acc_a = _make_account(client, h_a, "Src", "daily", "500.00")
    acc_b = _make_account(client, h_b, "Dst", "daily", "0.00")

    r = client.post("/api/v1/transactions", json={
        "account_id": acc_a["id"], "amount": "100.00", "type": "transfer",
        "destination_account_id": acc_b["id"], "transaction_date": _now_iso(),
    }, headers=h_a)
    assert r.status_code == 404


def test_patch_me_updates_annual_inflation_rate(client: TestClient) -> None:
    """PATCH /auth/me updates annual_inflation_rate and rejects out-of-range values."""
    h = _auth_headers(client, "inflation@example.com")

    r = client.patch("/api/v1/auth/me", json={"annual_inflation_rate": "3.50"}, headers=h)
    assert r.status_code == 200
    assert Decimal(str(r.json()["annual_inflation_rate"])) == Decimal("3.50")

    invalid = client.patch("/api/v1/auth/me", json={"annual_inflation_rate": "150.00"}, headers=h)
    assert invalid.status_code == 422
