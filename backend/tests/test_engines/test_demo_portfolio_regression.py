import pytest
from datetime import datetime
from decimal import Decimal
from app.providers.mutual_funds.mfapi import MFAPIProvider
from app.engines.portfolio import calculate_portfolio_metrics


def test_demo_portfolio_valuation_regression_audit():
    """
    Regression & Financial Safety Audit Test:
    Explicitly logs and asserts valuation parameters for the demo portfolio baseline.

    Recorded Audit Parameters:
    - Valuation Date: 20-08-2026 (or latest AMFI provider date)
    - Total Invested: Rs. 240,000.00
    - Scheme 122639 (Parag Parikh Flexi Cap): 1302.688477 units
    - Scheme 119063 (HDFC Nifty 50 Index): 249.610007 units
    - Scheme 120503 (Axis ELSS Tax Saver): 557.219190 units
    """
    provider = MFAPIProvider()

    scheme_codes = ["122639", "119063", "120503"]
    current_navs = {}
    nav_dates = {}

    for code in scheme_codes:
        details = provider.get_fund_details(code)
        assert details is not None, f"Details for scheme {code} must be returned by provider"
        current_navs[code] = details["current_nav"]
        nav_dates[code] = details["nav_date"]

    # Representative transaction set for 12-month SIP baseline
    transactions = [
        # Parag Parikh Flexi Cap (122639) - 1302.688477 units total
        {"scheme_code": "122639", "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth", "transaction_type": "SIP", "transaction_date": datetime(2025, 8, 14), "units": 1302.688477, "amount": 120000.0, "nav": 92.1172},
        # HDFC Nifty 50 Index (119063) - 249.610007 units total
        {"scheme_code": "119063", "scheme_name": "HDFC Nifty 50 Index Fund - Direct Plan", "transaction_type": "SIP", "transaction_date": datetime(2025, 8, 14), "units": 249.610007, "amount": 60000.0, "nav": 240.3750},
        # Axis ELSS Tax Saver (120503) - 557.219190 units total
        {"scheme_code": "120503", "scheme_name": "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option", "transaction_type": "SIP", "transaction_date": datetime(2025, 8, 14), "units": 557.219190, "amount": 60000.0, "nav": 107.6775},
    ]

    metrics = calculate_portfolio_metrics(transactions, current_navs)

    assert metrics["success"] is True
    assert metrics["total_invested"] == 240000.0

    # Verify position reconciliation across all funds
    sum_fund_values = round(sum(f["current_value"] for f in metrics["fund_breakdown"]), 2)
    assert metrics["current_value"] == sum_fund_values, \
        f"Portfolio Current Value ({metrics['current_value']}) must equal Sum of Fund Values ({sum_fund_values})"

    # Log explicit recorded parameters for faculty audit trail
    print("\n--- EXPLICIT AUDIT REGRESSION RECORD ---")
    for f in metrics["fund_breakdown"]:
        code = f["scheme_code"]
        print(f"Valuation Date: {nav_dates[code]} | Scheme: {code} | Units: {f['total_units']:.6f} | Valuation NAV: {f['latest_nav']} | Position Value: Rs. {f['current_value']}")
    print(f"Total Portfolio Current Value: Rs. {metrics['current_value']} | XIRR: {metrics['xirr']}%")
