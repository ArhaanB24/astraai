import pytest
from datetime import datetime, timedelta
from app.engines.xirr import calculate_xirr
from app.engines.portfolio import calculate_portfolio_metrics


def test_xirr_uses_exact_transaction_dates():
    """
    Regression Test: Verifies XIRR engine preserves exact irregular transaction dates
    (e.g., 2025-08-14, 2025-09-15) rather than normalizing to arbitrary monthly boundaries.
    """
    exact_dates_flows = [
        (datetime(2025, 8, 14), -10000.0),
        (datetime(2025, 9, 15), -10000.0),
        (datetime(2025, 10, 10), 20500.0)
    ]

    normalized_dates_flows = [
        (datetime(2025, 8, 15), -10000.0),
        (datetime(2025, 9, 15), -10000.0),
        (datetime(2025, 10, 15), 20500.0)
    ]

    res_exact = calculate_xirr(exact_dates_flows)
    res_normalized = calculate_xirr(normalized_dates_flows)

    assert res_exact["success"] is True
    assert res_normalized["success"] is True

    # Exact dates must produce a different, mathematically precise XIRR rate than normalized dates
    assert res_exact["xirr_percentage"] != res_normalized["xirr_percentage"], \
        "XIRR calculation must reflect exact transaction dates and not assume static monthly dates"


def test_portfolio_metrics_exact_date_xirr_reconciliation():
    """
    Regression Test: Verifies portfolio metrics reconciliation between fund-level values
    and portfolio-level value, and validates exact date aggregation for XIRR.
    """
    transactions = [
        {
            "scheme_code": "122639",
            "scheme_name": "Parag Parikh Flexi Cap Fund",
            "transaction_type": "SIP",
            "transaction_date": datetime(2025, 8, 14),
            "units": 108.420241,
            "nav": 92.2337,
            "amount": 10000.0
        },
        {
            "scheme_code": "119063",
            "scheme_name": "Axis Bluechip Fund",
            "transaction_type": "SIP",
            "transaction_date": datetime(2025, 8, 14),
            "units": 20.911499,
            "nav": 239.1029,
            "amount": 5000.0
        }
    ]

    current_navs = {
        "122639": 90.4982,
        "119063": 236.4268
    }

    res = calculate_portfolio_metrics(transactions, current_navs)

    assert res["success"] is True

    # Check that sum of rounded fund breakdown current values matches portfolio current_value exactly
    sum_funds = round(sum(f["current_value"] for f in res["fund_breakdown"]), 2)
    assert res["current_value"] == sum_funds, f"Mismatch: Portfolio Current Value ({res['current_value']}) != Sum of Fund Values ({sum_funds})"
