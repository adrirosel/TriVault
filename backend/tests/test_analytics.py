"""Analytics: summary, cash flow (transfers excluded), inflation erosion, fund real return, tx filters."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.models.user import User
from app.services import analytics_service
from tests.helpers import API, auth_headers, contribute, make_account, make_category, make_fund


def _tx(client: TestClient, h: dict, **fields) -> dict:
    r = client.post(f"{API}/transactions", json=fields, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def test_summary_includes_fund_market_value_in_investment_bucket(client: TestClient) -> None:
    h = auth_headers(client, "ansummary@example.com")
    make_account(client, h, "Diaria", "daily", "1200.00")
    make_account(client, h, "Colchón", "emergency", "3000.00")
    inv = make_account(client, h, "Broker", "investment", "1000.00")
    fund = make_fund(client, h, inv["id"])
    contribute(client, h, fund["id"], shares="10", purchase_nav="50", gross_amount="500.00", fee="2.00")
    client.patch(f"{API}/funds/{fund['id']}", json={"current_nav": "55"}, headers=h)

    body = client.get(f"{API}/analytics/summary", headers=h).json()
    buckets = {b["bucket_type"]: b for b in body["buckets"]}
    assert Decimal(buckets["investment"]["cash"]) == Decimal("498.00")
    assert Decimal(buckets["investment"]["funds_value"]) == Decimal("550.00")
    assert Decimal(buckets["investment"]["total"]) == Decimal("1048.00")
    assert Decimal(body["net_worth"]) == Decimal("5248.00")


def test_cashflow_excludes_transfers_and_computes_savings_rate(client: TestClient) -> None:
    h = auth_headers(client, "ancash@example.com")
    daily = make_account(client, h, "Diaria", "daily", "0.00")
    emergency = make_account(client, h, "Colchón", "emergency", "0.00")
    salary = make_category(client, h, "Nómina", "income")
    rent = make_category(client, h, "Alquiler", "expense", is_fixed=True)
    food = make_category(client, h, "Comida", "expense")
    when = "2026-10-15T10:00:00Z"

    _tx(client, h, account_id=daily["id"], type="income", amount="2000.00", category_id=salary["id"], transaction_date=when)
    _tx(client, h, account_id=daily["id"], type="expense", amount="800.00", category_id=rent["id"], transaction_date=when)
    _tx(client, h, account_id=daily["id"], type="expense", amount="300.00", category_id=food["id"], transaction_date=when)
    _tx(client, h, account_id=daily["id"], type="transfer", amount="500.00",
        destination_account_id=emergency["id"], transaction_date=when)
    # Outside the period: must be ignored.
    _tx(client, h, account_id=daily["id"], type="expense", amount="999.00", category_id=food["id"],
        transaction_date="2026-09-30T21:59:00Z")

    params = {"date_from": "2026-10-01T00:00:00+02:00", "date_to": "2026-11-01T00:00:00+01:00"}
    body = client.get(f"{API}/analytics/cashflow", params=params, headers=h).json()
    assert Decimal(body["income"]) == Decimal("2000.00")
    assert Decimal(body["expense"]) == Decimal("1100.00")
    assert Decimal(body["net"]) == Decimal("900.00")
    assert Decimal(body["savings_rate"]) == Decimal("45.00")
    assert Decimal(body["fixed_expense"]) == Decimal("800.00")
    assert Decimal(body["variable_expense"]) == Decimal("300.00")
    assert [c["name"] for c in body["by_category"]] == ["Nómina", "Alquiler", "Comida"]


def test_cashflow_without_income_has_null_savings_rate_and_monthly_series(client: TestClient) -> None:
    h = auth_headers(client, "ancashnull@example.com")
    daily = make_account(client, h, "Diaria", "daily", "100.00")
    food = make_category(client, h, "Comida", "expense")
    _tx(client, h, account_id=daily["id"], type="expense", amount="12.50", category_id=food["id"],
        transaction_date=datetime.now(UTC).isoformat())

    body = client.get(f"{API}/analytics/cashflow", params={"months": 3}, headers=h).json()
    assert body["savings_rate"] is None
    assert Decimal(body["expense"]) == Decimal("12.50")
    assert len(body["monthly"]) == 3
    assert Decimal(body["monthly"][-1]["expense"]) == Decimal("12.50")


def test_cashflow_rejects_naive_dates_and_bad_timezone(client: TestClient) -> None:
    h = auth_headers(client, "ancashbad@example.com")
    assert client.get(f"{API}/analytics/cashflow", params={"date_from": "2026-10-01T00:00:00"}, headers=h).status_code == 422
    assert client.get(f"{API}/analytics/cashflow", params={"tz": "Mars/Base"}, headers=h).status_code == 422


def test_inflation_erosion_on_liquid_money_only(client: TestClient) -> None:
    h = auth_headers(client, "aninfl@example.com")
    client.patch(f"{API}/auth/me", json={"annual_inflation_rate": "3.00"}, headers=h)
    make_account(client, h, "Diaria", "daily", "1200.00")
    make_account(client, h, "Colchón", "emergency", "6000.00")
    make_account(client, h, "Broker", "investment", "10000.00")

    body = client.get(f"{API}/analytics/inflation", headers=h).json()
    assert Decimal(body["liquid_balance"]) == Decimal("7200.00")
    assert Decimal(body["annual_loss"]) == Decimal("216.00")
    assert Decimal(body["monthly_loss"]) == Decimal("18.00")


def test_fund_real_return_against_inflation(client: TestClient, db_session) -> None:
    h = auth_headers(client, "anfunds@example.com")
    client.patch(f"{API}/auth/me", json={"annual_inflation_rate": "2.00"}, headers=h)
    inv = make_account(client, h, "Broker", "investment", "0.00")
    fund = make_fund(client, h, inv["id"])
    today = date(2026, 11, 27)
    four_years_ago = today - timedelta(days=1461)  # exactly 4 * 365.25 days
    contribute(client, h, fund["id"], operation_date=four_years_ago.isoformat(), shares="100",
               purchase_nav="10", gross_amount="1000.00", affects_cash=False)
    client.patch(f"{API}/funds/{fund['id']}", json={"current_nav": "10.50"}, headers=h)

    user = db_session.query(User).filter(User.email == "anfunds@example.com").one()
    result = analytics_service.funds(db_session, user, today=today)
    perf = result.positions[0]
    assert perf.market_value == Decimal("1050.00")
    assert perf.nominal_gain == Decimal("50.00")
    assert perf.nominal_return_pct == Decimal("5.00")
    assert perf.inflation_adjusted_cost == Decimal("1082.43")  # 1000 * 1.02^4
    assert perf.accumulated_inflation_pct == Decimal("8.24")
    assert perf.real_gain == Decimal("-32.43")  # +5 % nominal does not beat 4 years of 2 % inflation
    assert perf.beats_inflation is False
    assert result.beats_inflation is False

    # The endpoint answers with the same shape for today's date.
    assert client.get(f"{API}/analytics/funds", headers=h).status_code == 200


def test_transaction_list_filters_and_pagination(client: TestClient) -> None:
    h = auth_headers(client, "txfilters@example.com")
    daily = make_account(client, h, "Diaria", "daily", "1000.00")
    emergency = make_account(client, h, "Colchón", "emergency", "0.00")
    food = make_category(client, h, "Comida", "expense")
    _tx(client, h, account_id=daily["id"], type="expense", amount="1.00", category_id=food["id"],
        transaction_date="2026-10-01T10:00:00Z")
    _tx(client, h, account_id=daily["id"], type="expense", amount="2.00", category_id=food["id"],
        transaction_date="2026-10-20T10:00:00Z")
    _tx(client, h, account_id=daily["id"], type="transfer", amount="3.00", destination_account_id=emergency["id"],
        transaction_date="2026-10-25T10:00:00Z")

    def amounts(**params) -> list[str]:
        return [t["amount"] for t in client.get(f"{API}/transactions", params=params, headers=h).json()]

    assert amounts(type="expense") == ["2.00", "1.00"]
    assert amounts(date_from="2026-10-15T00:00:00Z", date_to="2026-10-26T00:00:00Z") == ["3.00", "2.00"]
    assert amounts(account_id=emergency["id"]) == ["3.00"]  # destination side counts
    assert amounts(category_id=food["id"], limit=1, offset=1) == ["1.00"]
