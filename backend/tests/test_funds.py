"""Fund positions and contributions: ownership, broker cash, average cost, atomicity."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.schemas.fund import isin_is_valid
from tests.helpers import API, auth_headers, balance, contribute, make_account, make_fund


def _fund(client: TestClient, h: dict, fund_id: int) -> dict:
    return client.get(f"{API}/funds/{fund_id}", headers=h).json()


def test_isin_checksum() -> None:
    assert isin_is_valid("IE00B4L5Y983")
    assert isin_is_valid("US0378331005")
    assert not isin_is_valid("IE00B4L5Y984")  # wrong check digit
    assert not isin_is_valid("IE00B4L5Y98")  # too short


def test_position_requires_owned_investment_account(client: TestClient) -> None:
    h = auth_headers(client, "fundacc@example.com")
    other = auth_headers(client, "fundacc-other@example.com")
    daily = make_account(client, h, "Diaria", "daily")
    foreign = make_account(client, other, "Broker ajeno", "investment")
    inv = make_account(client, h, "Broker", "investment")

    body = {"isin": "IE00B4L5Y983", "fund_name": "MSCI World"}
    assert client.post(f"{API}/funds", json={**body, "account_id": daily["id"]}, headers=h).status_code == 422
    assert client.post(f"{API}/funds", json={**body, "account_id": foreign["id"]}, headers=h).status_code == 404
    bad_isin = {**body, "account_id": inv["id"], "isin": "IE00B4L5Y984"}
    assert client.post(f"{API}/funds", json=bad_isin, headers=h).status_code == 422
    assert client.post(f"{API}/funds", json={**body, "account_id": inv["id"]}, headers=h).status_code == 201
    # Same ISIN twice in the same account -> 409
    assert client.post(f"{API}/funds", json={**body, "account_id": inv["id"]}, headers=h).status_code == 409


def test_buy_and_sell_move_broker_cash_and_average_cost(client: TestClient) -> None:
    h = auth_headers(client, "fundbuy@example.com")
    inv = make_account(client, h, "Broker", "investment", "1000.00")
    fund = make_fund(client, h, inv["id"])

    r = contribute(client, h, fund["id"], shares="10.0000", purchase_nav="50.0000", gross_amount="500.00", fee="2.00")
    assert r.status_code == 201, r.text
    assert balance(client, h, inv["id"]) == Decimal("498.00")
    pos = _fund(client, h, fund["id"])
    assert Decimal(pos["shares"]) == Decimal("10")
    assert Decimal(pos["total_invested"]) == Decimal("502.00")
    assert Decimal(pos["current_nav"]) == Decimal("50")  # first NAV taken from the purchase
    assert Decimal(pos["market_value"]) == Decimal("500.00")

    # Sell 4 shares at 60 with 1 € fee: cash +239, cost basis reduced by 40 % of 502 = 200.80
    r = contribute(client, h, fund["id"], order_type="sell", operation_date="2026-03-01",
                   shares="4.0000", purchase_nav="60.0000", gross_amount="240.00", fee="1.00")
    assert r.status_code == 201, r.text
    assert balance(client, h, inv["id"]) == Decimal("737.00")
    pos = _fund(client, h, fund["id"])
    assert Decimal(pos["shares"]) == Decimal("6")
    assert Decimal(pos["total_invested"]) == Decimal("301.20")


def test_sell_more_than_held_and_insufficient_cash_are_rejected(client: TestClient) -> None:
    h = auth_headers(client, "fundrules@example.com")
    inv = make_account(client, h, "Broker", "investment", "100.00")
    fund = make_fund(client, h, inv["id"])

    too_expensive = contribute(client, h, fund["id"], shares="5", purchase_nav="50", gross_amount="250.00")
    assert too_expensive.status_code == 422
    assert balance(client, h, inv["id"]) == Decimal("100.00")

    oversell = contribute(client, h, fund["id"], order_type="sell", shares="1", purchase_nav="50", gross_amount="50.00")
    assert oversell.status_code == 422
    assert Decimal(_fund(client, h, fund["id"])["shares"]) == Decimal("0")


def test_historical_position_does_not_touch_cash(client: TestClient) -> None:
    h = auth_headers(client, "fundhist@example.com")
    inv = make_account(client, h, "Broker", "investment", "0.00")
    fund = make_fund(client, h, inv["id"])

    r = contribute(client, h, fund["id"], shares="20", purchase_nav="40", gross_amount="800.00", affects_cash=False)
    assert r.status_code == 201, r.text
    assert r.json()["affects_cash"] is False
    assert balance(client, h, inv["id"]) == Decimal("0.00")
    assert Decimal(_fund(client, h, fund["id"])["total_invested"]) == Decimal("800.00")


def test_delete_contribution_reverts_and_protects_later_sells(client: TestClient) -> None:
    h = auth_headers(client, "funddel@example.com")
    inv = make_account(client, h, "Broker", "investment", "1000.00")
    fund = make_fund(client, h, inv["id"])
    buy = contribute(client, h, fund["id"], shares="10", purchase_nav="50", gross_amount="500.00", fee="2.00").json()
    sell = contribute(client, h, fund["id"], order_type="sell", operation_date="2026-02-01",
                      shares="5", purchase_nav="55", gross_amount="275.00").json()

    base = f"{API}/funds/{fund['id']}/contributions"
    # Deleting the buy would leave the later sell uncovered -> 422, nothing changes.
    assert client.delete(f"{base}/{buy['id']}", headers=h).status_code == 422
    assert balance(client, h, inv["id"]) == Decimal("773.00")

    assert client.delete(f"{base}/{sell['id']}", headers=h).status_code == 204
    assert balance(client, h, inv["id"]) == Decimal("498.00")
    assert client.delete(f"{base}/{buy['id']}", headers=h).status_code == 204
    assert balance(client, h, inv["id"]) == Decimal("1000.00")
    pos = _fund(client, h, fund["id"])
    assert Decimal(pos["shares"]) == 0 and Decimal(pos["total_invested"]) == 0

    # Position without history can now be deleted.
    assert client.delete(f"{API}/funds/{fund['id']}", headers=h).status_code == 204


def test_delete_position_with_history_is_blocked(client: TestClient) -> None:
    h = auth_headers(client, "funddelpos@example.com")
    inv = make_account(client, h, "Broker", "investment", "100.00")
    fund = make_fund(client, h, inv["id"])
    contribute(client, h, fund["id"], shares="1", purchase_nav="10", gross_amount="10.00")
    assert client.delete(f"{API}/funds/{fund['id']}", headers=h).status_code == 409


def test_patch_only_updates_name_and_nav(client: TestClient) -> None:
    h = auth_headers(client, "fundpatch@example.com")
    inv = make_account(client, h, "Broker", "investment", "100.00")
    fund = make_fund(client, h, inv["id"], nav="10")

    r = client.patch(f"{API}/funds/{fund['id']}", json={"current_nav": "12.3456", "fund_name": "Nuevo"}, headers=h)
    assert r.status_code == 200
    assert Decimal(r.json()["current_nav"]) == Decimal("12.3456")
    assert client.patch(f"{API}/funds/{fund['id']}", json={"shares": "999"}, headers=h).status_code == 422
    assert client.patch(f"{API}/funds/{fund['id']}", json={"current_nav": "0"}, headers=h).status_code == 422


def test_fund_idor(client: TestClient) -> None:
    h_a = auth_headers(client, "fundidora@example.com")
    h_b = auth_headers(client, "fundidorb@example.com")
    inv = make_account(client, h_a, "Broker", "investment", "100.00")
    fund = make_fund(client, h_a, inv["id"])
    c = contribute(client, h_a, fund["id"], shares="1", purchase_nav="10", gross_amount="10.00").json()

    assert client.get(f"{API}/funds/{fund['id']}", headers=h_b).status_code == 404
    assert client.patch(f"{API}/funds/{fund['id']}", json={"current_nav": "1"}, headers=h_b).status_code == 404
    assert client.get(f"{API}/funds/{fund['id']}/contributions", headers=h_b).status_code == 404
    assert contribute(client, h_b, fund["id"], shares="1", purchase_nav="1", gross_amount="1.00").status_code == 404
    assert client.delete(f"{API}/funds/{fund['id']}/contributions/{c['id']}", headers=h_b).status_code == 404
    assert client.get(f"{API}/funds", headers=h_b).json() == []
    assert balance(client, h_a, inv["id"]) == Decimal("90.00")


def test_contribution_failure_midway_rolls_back(client: TestClient, monkeypatch) -> None:
    from app.services import fund_service

    h = auth_headers(client, "fundrollback@example.com")
    inv = make_account(client, h, "Broker", "investment", "1000.00")
    fund = make_fund(client, h, inv["id"])

    def crash(position, contributions):
        position.shares = Decimal("999")
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(fund_service, "_apply_position_state", crash)
    with pytest.raises(RuntimeError):
        contribute(client, h, fund["id"], shares="1", purchase_nav="10", gross_amount="10.00")
    monkeypatch.undo()

    assert balance(client, h, inv["id"]) == Decimal("1000.00")
    assert Decimal(_fund(client, h, fund["id"])["shares"]) == 0
    assert client.get(f"{API}/funds/{fund['id']}/contributions", headers=h).json() == []


def test_backdated_buy_is_replayed_in_date_order(client: TestClient) -> None:
    """A sell recorded before its (back-dated) buy is accepted once the buy exists earlier in time."""
    h = auth_headers(client, "fundorder@example.com")
    inv = make_account(client, h, "Broker", "investment", "1000.00")
    fund = make_fund(client, h, inv["id"])
    contribute(client, h, fund["id"], operation_date="2026-02-01", shares="10", purchase_nav="10", gross_amount="100.00")
    contribute(client, h, fund["id"], operation_date="2026-03-01", order_type="sell",
               shares="10", purchase_nav="12", gross_amount="120.00")
    # Back-dated buy before everything: replay must stay valid and keep 5 shares at its cost.
    r = contribute(client, h, fund["id"], operation_date="2026-01-01", shares="5", purchase_nav="8", gross_amount="40.00")
    assert r.status_code == 201, r.text
    pos = _fund(client, h, fund["id"])
    assert Decimal(pos["shares"]) == Decimal("5")
    # Average cost: (40 + 100) / 15 per share; 10 sold -> remaining 5 * 9.333 = 46.67
    assert Decimal(pos["total_invested"]) == Decimal("46.67")
