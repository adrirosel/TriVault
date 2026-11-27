"""Accounts CRUD, Decimal precision, balance invariants, and IDOR negative tests."""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import CategoryType, TransactionType
from app.models.transaction import Transaction


def _register_and_get_headers(client: TestClient, email: str) -> dict[str, str]:
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "ValidPassword123!"},
    )
    assert reg.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ValidPassword123!"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_create_three_buckets_with_decimal_precision(client: TestClient) -> None:
    """User can create daily, emergency, and investment accounts with exact Decimal balances."""
    headers = _register_and_get_headers(client, "buckets@example.com")

    payloads = [
        {"name": "Cuenta Corriente", "bucket_type": "daily", "initial_balance": "0.10"},
        {"name": "Colchón", "bucket_type": "emergency", "initial_balance": "0.20"},
        {"name": "Indexados", "bucket_type": "investment", "initial_balance": "1500.55"},
    ]
    created = []
    for item in payloads:
        resp = client.post("/api/v1/accounts", json=item, headers=headers)
        assert resp.status_code == 201
        created.append(resp.json())

    assert [acc["bucket_type"] for acc in created] == ["daily", "emergency", "investment"]
    liquid_sum = Decimal(str(created[0]["current_balance"])) + Decimal(
        str(created[1]["current_balance"])
    )
    assert liquid_sum == Decimal("0.30")

    neg_resp = client.post(
        "/api/v1/accounts",
        json={"name": "Negativa", "bucket_type": "daily", "initial_balance": "-1.00"},
        headers=headers,
    )
    assert neg_resp.status_code == 422


def test_only_eur_currency_is_accepted(client: TestClient) -> None:
    """Multi-currency is out of scope: non-EUR accounts are rejected, lowercase eur is normalized."""
    headers = _register_and_get_headers(client, "currency@example.com")

    usd = client.post(
        "/api/v1/accounts",
        json={"name": "USD", "bucket_type": "daily", "currency": "USD"},
        headers=headers,
    )
    assert usd.status_code == 422

    eur = client.post(
        "/api/v1/accounts",
        json={"name": "EUR", "bucket_type": "daily", "currency": "eur"},
        headers=headers,
    )
    assert eur.status_code == 201
    assert eur.json()["currency"] == "EUR"


def test_patch_account_blocks_direct_balance_modification(client: TestClient) -> None:
    """PATCH /accounts/{id} updates metadata only and rejects direct balance tampering."""
    headers = _register_and_get_headers(client, "invariant@example.com")
    create_resp = client.post(
        "/api/v1/accounts",
        json={"name": "Diaria", "bucket_type": "daily", "initial_balance": "250.00"},
        headers=headers,
    )
    account_id = create_resp.json()["id"]

    tamper_resp = client.patch(
        f"/api/v1/accounts/{account_id}",
        json={"current_balance": "99999.00"},
        headers=headers,
    )
    assert tamper_resp.status_code == 422

    ok_resp = client.patch(
        f"/api/v1/accounts/{account_id}",
        json={"name": "Diaria Principal", "bucket_type": "emergency"},
        headers=headers,
    )
    assert ok_resp.status_code == 200
    assert ok_resp.json()["name"] == "Diaria Principal"
    assert ok_resp.json()["bucket_type"] == "emergency"
    assert Decimal(str(ok_resp.json()["current_balance"])) == Decimal("250.00")


def test_idor_prevents_cross_user_read_update_and_delete(client: TestClient) -> None:
    """User B cannot read, update, or delete User A's accounts and receives 404."""
    headers_a = _register_and_get_headers(client, "usera@example.com")
    headers_b = _register_and_get_headers(client, "userb@example.com")

    create_resp = client.post(
        "/api/v1/accounts",
        json={"name": "Privada A", "bucket_type": "daily", "initial_balance": "500.00"},
        headers=headers_a,
    )
    account_a_id = create_resp.json()["id"]

    assert client.get(f"/api/v1/accounts/{account_a_id}", headers=headers_b).status_code == 404
    assert (
        client.patch(
            f"/api/v1/accounts/{account_a_id}",
            json={"name": "Hackeada"},
            headers=headers_b,
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/accounts/{account_a_id}", headers=headers_b).status_code == 404

    list_b = client.get("/api/v1/accounts", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json() == []

    get_a = client.get(f"/api/v1/accounts/{account_a_id}", headers=headers_a)
    assert get_a.status_code == 200
    assert get_a.json()["name"] == "Privada A"


def test_delete_account_blocks_when_history_exists_and_allows_when_empty(
    client: TestClient,
    db_session: Session,
) -> None:
    """DELETE returns 409 Conflict if transactions exist and 204 if account is empty."""
    headers = _register_and_get_headers(client, "history@example.com")
    me = client.get("/api/v1/auth/me", headers=headers).json()
    user_id = me["id"]

    empty_acc = client.post(
        "/api/v1/accounts",
        json={"name": "Vacia", "bucket_type": "daily"},
        headers=headers,
    ).json()
    used_acc = client.post(
        "/api/v1/accounts",
        json={"name": "Con Movimientos", "bucket_type": "daily", "initial_balance": "100.00"},
        headers=headers,
    ).json()

    category = Category(user_id=user_id, name="Salario", type=CategoryType.INCOME, is_fixed=True)
    db_session.add(category)
    db_session.flush()

    tx = Transaction(
        user_id=user_id,
        account_id=used_acc["id"],
        category_id=category.id,
        amount=Decimal("50.00"),
        type=TransactionType.INCOME,
        description="Ingreso prueba",
        transaction_date=datetime.now(UTC),
    )
    db_session.add(tx)
    db_session.commit()

    assert client.delete(f"/api/v1/accounts/{used_acc['id']}", headers=headers).status_code == 409
    assert client.delete(f"/api/v1/accounts/{empty_acc['id']}", headers=headers).status_code == 204
