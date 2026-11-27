"""Transaction atomicity, balance invariants, IDOR, and cross-account transfer tests."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
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
    return datetime.now(UTC).isoformat()


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


# ---------------------------------------------------------------------------
# Rollback, category-type, currency and full-edit coverage (Fase 1 gate)
# ---------------------------------------------------------------------------

def _balance(client: TestClient, headers: dict, account_id: int) -> Decimal:
    body = client.get(f"/api/v1/accounts/{account_id}", headers=headers).json()
    return Decimal(str(body["current_balance"]))


def _post_tx(client: TestClient, headers: dict, **fields) -> dict:
    r = client.post("/api/v1/transactions", json={"transaction_date": _now_iso(), **fields}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_transfer_failure_midway_rolls_back_both_balances(client: TestClient, monkeypatch) -> None:
    """If the transfer fails after debiting the source, neither balance nor the row persists."""
    from app.services import transaction_service

    h = _auth_headers(client, "txrollback@example.com")
    src = _make_account(client, h, "Origen", "daily", "800.00")
    dst = _make_account(client, h, "Destino", "emergency", "200.00")

    def debit_source_then_crash(accounts, tx_type, account_id, destination_id, amount, sign):
        accounts[account_id].current_balance -= amount * sign
        raise RuntimeError("fallo simulado a mitad de la transferencia")

    monkeypatch.setattr(transaction_service, "_apply_effect", debit_source_then_crash)
    with pytest.raises(RuntimeError):
        client.post("/api/v1/transactions", json={
            "account_id": src["id"], "amount": "300.00", "type": "transfer",
            "destination_account_id": dst["id"], "transaction_date": _now_iso(),
        }, headers=h)
    monkeypatch.undo()

    assert _balance(client, h, src["id"]) == Decimal("800.00")
    assert _balance(client, h, dst["id"]) == Decimal("200.00")
    assert client.get("/api/v1/transactions", headers=h).json() == []


def test_category_type_must_match_transaction_type(client: TestClient) -> None:
    h = _auth_headers(client, "txcattype@example.com")
    acc = _make_account(client, h, "Cuenta", "daily", "100.00")
    cat_inc = _make_category(client, h, "Nomina", "income")
    cat_exp = _make_category(client, h, "Super", "expense")

    for tx_type, category in (("expense", cat_inc), ("income", cat_exp)):
        r = client.post("/api/v1/transactions", json={
            "account_id": acc["id"], "amount": "10.00", "type": tx_type,
            "category_id": category["id"], "transaction_date": _now_iso(),
        }, headers=h)
        assert r.status_code == 422
    assert _balance(client, h, acc["id"]) == Decimal("100.00")


def test_transfer_between_different_currencies_is_rejected(client: TestClient, db_session) -> None:
    """Defence in depth: legacy non-EUR accounts cannot be mixed in a transfer."""
    from app.models.account import Account

    h = _auth_headers(client, "txcurrency@example.com")
    src = _make_account(client, h, "EUR", "daily", "100.00")
    dst = _make_account(client, h, "Legacy USD", "investment", "0.00")
    db_session.get(Account, dst["id"]).currency = "USD"
    db_session.commit()

    r = client.post("/api/v1/transactions", json={
        "account_id": src["id"], "amount": "10.00", "type": "transfer",
        "destination_account_id": dst["id"], "transaction_date": _now_iso(),
    }, headers=h)
    assert r.status_code == 422
    assert _balance(client, h, src["id"]) == Decimal("100.00")


def test_update_amount_adjusts_balance(client: TestClient) -> None:
    h = _auth_headers(client, "txupdamount@example.com")
    acc = _make_account(client, h, "Cuenta", "daily", "1000.00")
    cat = _make_category(client, h, "Ocio", "expense")
    tx = _post_tx(client, h, account_id=acc["id"], amount="100.00", type="expense", category_id=cat["id"])
    assert _balance(client, h, acc["id"]) == Decimal("900.00")

    r = client.patch(f"/api/v1/transactions/{tx['id']}", json={"amount": "40.50"}, headers=h)
    assert r.status_code == 200
    assert Decimal(str(r.json()["amount"])) == Decimal("40.50")
    assert _balance(client, h, acc["id"]) == Decimal("959.50")


def test_update_source_account_moves_balance_effect(client: TestClient) -> None:
    h = _auth_headers(client, "txupdaccount@example.com")
    old = _make_account(client, h, "Vieja", "daily", "500.00")
    new = _make_account(client, h, "Nueva", "emergency", "500.00")
    cat = _make_category(client, h, "Bonus", "income")
    tx = _post_tx(client, h, account_id=old["id"], amount="200.00", type="income", category_id=cat["id"])

    r = client.patch(f"/api/v1/transactions/{tx['id']}", json={"account_id": new["id"]}, headers=h)
    assert r.status_code == 200
    assert _balance(client, h, old["id"]) == Decimal("500.00")
    assert _balance(client, h, new["id"]) == Decimal("700.00")


def test_update_expense_to_transfer(client: TestClient) -> None:
    h = _auth_headers(client, "txupdtype@example.com")
    src = _make_account(client, h, "Diaria", "daily", "1000.00")
    dst = _make_account(client, h, "Colchon", "emergency", "0.00")
    cat = _make_category(client, h, "Varios", "expense")
    tx = _post_tx(client, h, account_id=src["id"], amount="300.00", type="expense", category_id=cat["id"])

    # Missing destination / keeping category -> invalid shape, balances untouched.
    bad = client.patch(f"/api/v1/transactions/{tx['id']}", json={"type": "transfer"}, headers=h)
    assert bad.status_code == 422
    assert _balance(client, h, src["id"]) == Decimal("700.00")

    r = client.patch(f"/api/v1/transactions/{tx['id']}", json={
        "type": "transfer", "category_id": None, "destination_account_id": dst["id"],
    }, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["category_id"] is None
    assert body["destination_account_id"] == dst["id"]
    assert _balance(client, h, src["id"]) == Decimal("700.00")
    assert _balance(client, h, dst["id"]) == Decimal("300.00")

    # Deleting the edited transfer restores both accounts.
    assert client.delete(f"/api/v1/transactions/{tx['id']}", headers=h).status_code == 204
    assert _balance(client, h, src["id"]) == Decimal("1000.00")
    assert _balance(client, h, dst["id"]) == Decimal("0.00")


def test_update_with_foreign_resources_or_nulls_is_rejected(client: TestClient) -> None:
    h_a = _auth_headers(client, "txupdidora@example.com")
    h_b = _auth_headers(client, "txupdidorb@example.com")
    acc_a = _make_account(client, h_a, "A", "daily", "500.00")
    cat_a = _make_category(client, h_a, "Comida", "expense")
    acc_b = _make_account(client, h_b, "B", "daily", "500.00")
    cat_b = _make_category(client, h_b, "Comida", "expense")
    tx = _post_tx(client, h_a, account_id=acc_a["id"], amount="50.00", type="expense", category_id=cat_a["id"])

    url = f"/api/v1/transactions/{tx['id']}"
    assert client.patch(url, json={"account_id": acc_b["id"]}, headers=h_a).status_code == 404
    assert client.patch(url, json={"category_id": cat_b["id"]}, headers=h_a).status_code == 404
    assert client.patch(url, json={"amount": "1.00"}, headers=h_b).status_code == 404
    assert client.patch(url, json={"amount": None}, headers=h_a).status_code == 422
    assert client.patch(url, json={"amount": "-5.00"}, headers=h_a).status_code == 422

    assert _balance(client, h_a, acc_a["id"]) == Decimal("450.00")
    assert _balance(client, h_b, acc_b["id"]) == Decimal("500.00")
