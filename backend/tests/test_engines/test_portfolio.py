import pytest
from datetime import datetime, timedelta
from app.engines.portfolio import calculate_portfolio_metrics


def test_portfolio_metrics_aggregation():
    base_date = datetime(2023, 1, 1)
    transactions = [
        {
            "scheme_code": "122639",
            "scheme_name": "Parag Parikh Flexi Cap Fund",
            "transaction_type": "SIP",
            "transaction_date": base_date,
            "units": 100.0,
            "nav": 50.0,
            "amount": 5000.0
        },
        {
            "scheme_code": "122639",
            "scheme_name": "Parag Parikh Flexi Cap Fund",
            "transaction_type": "SIP",
            "transaction_date": base_date + timedelta(days=30),
            "units": 100.0,
            "nav": 50.0,
            "amount": 5000.0
        }
    ]

    current_navs = {"122639": 60.0}  # Latest NAV is ₹60
    res = calculate_portfolio_metrics(transactions, current_navs)

    assert res["success"] is True
    assert res["total_invested"] == 10000.0
    assert res["current_value"] == 12000.0  # 200 units * 60 NAV
    assert res["total_profit_loss"] == 2000.0
    assert res["profit_loss_percentage"] == 20.0
    assert len(res["fund_breakdown"]) == 1
    assert res["fund_breakdown"][0]["allocation_pct"] == 100.0
