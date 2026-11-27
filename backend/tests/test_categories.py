"""Category CRUD and IDOR negative tests."""

from datetime import UTC

from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, email: str) -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": "ValidPass123!"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "ValidPass123!"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_create_income_and_expense_categories(client: TestClient) -> None:
    """User can create income and expense categories; duplicates return 409."""
    h = _auth_headers(client, "catuser@example.com")

    r1 = client.post("/api/v1/categories", json={"name": "Salario", "type": "income", "is_fixed": True}, headers=h)
    assert r1.status_code == 201
    assert r1.json()["type"] == "income"

    r2 = client.post("/api/v1/categories", json={"name": "Alimentación", "type": "expense"}, headers=h)
    assert r2.status_code == 201

    # Duplicate name + type → 409
    dup = client.post("/api/v1/categories", json={"name": "Salario", "type": "income"}, headers=h)
    assert dup.status_code == 409

    # Same name but different type is allowed
    ok = client.post("/api/v1/categories", json={"name": "Salario", "type": "expense"}, headers=h)
    assert ok.status_code == 201


def test_category_patch_and_idor(client: TestClient) -> None:
    """PATCH updates only allowed fields; User B cannot see or modify User A's categories."""
    h_a = _auth_headers(client, "cata@example.com")
    h_b = _auth_headers(client, "catb@example.com")

    cat = client.post("/api/v1/categories", json={"name": "Ocio", "type": "expense"}, headers=h_a).json()
    cat_id = cat["id"]

    patch = client.patch(f"/api/v1/categories/{cat_id}", json={"is_fixed": True}, headers=h_a)
    assert patch.status_code == 200
    assert patch.json()["is_fixed"] is True

    assert client.get(f"/api/v1/categories/{cat_id}", headers=h_b).status_code == 404
    assert client.patch(f"/api/v1/categories/{cat_id}", json={"name": "Hackeada"}, headers=h_b).status_code == 404
    assert client.delete(f"/api/v1/categories/{cat_id}", headers=h_b).status_code == 404


def test_delete_category_blocked_when_has_transactions(
    client: TestClient,
) -> None:
    """Cannot delete a category that has linked transactions; deletes fine when empty."""
    from datetime import datetime


    h = _auth_headers(client, "catdelete@example.com")

    # Create account and two categories
    acc = client.post(
        "/api/v1/accounts",
        json={"name": "Diaria", "bucket_type": "daily", "initial_balance": "200.00"},
        headers=h,
    ).json()
    cat_used = client.post("/api/v1/categories", json={"name": "Supermercado", "type": "expense"}, headers=h).json()
    cat_empty = client.post("/api/v1/categories", json={"name": "Viajes", "type": "expense"}, headers=h).json()

    # Attach a transaction to cat_used via the API
    tx_payload = {
        "account_id": acc["id"],
        "amount": "50.00",
        "type": "expense",
        "category_id": cat_used["id"],
        "transaction_date": datetime.now(UTC).isoformat(),
    }
    tx = client.post("/api/v1/transactions", json=tx_payload, headers=h)
    assert tx.status_code == 201

    assert client.delete(f"/api/v1/categories/{cat_used['id']}", headers=h).status_code == 409
    assert client.delete(f"/api/v1/categories/{cat_empty['id']}", headers=h).status_code == 204
