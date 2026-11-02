import pytest
from decimal import Decimal
from app.providers.mutual_funds.mfapi import MFAPIProvider
from app.engines.portfolio import calculate_portfolio_metrics, _to_decimal


def test_scheme_identity_canonical_mapping():
    """
    Regression Test: Asserts scheme_code maps to authoritative canonical scheme identity
    returned directly by AMFI provider.
    """
    provider = MFAPIProvider()

    expected_identities = {
        "122639": {
            "name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
            "fund_house": "PPFAS Mutual Fund"
        },
        "119063": {
            "name": "HDFC Nifty 50 Index Fund - Direct Plan - Growth Option",
            "fund_house": "HDFC Mutual Fund"
        },
        "120503": {
            "name": "Axis ELSS- Tax Saver Fund - Direct Plan - Growth Option",
            "fund_house": "Axis Mutual Fund"
        }
    }

    for code, expected in expected_identities.items():
        details = provider.get_fund_details(code)
        assert details is not None, f"Scheme details for code {code} must be returned by provider"
        assert details["scheme_name"] == expected["name"], \
            f"Scheme name mismatch for {code}: Expected '{expected['name']}', Got '{details['scheme_name']}'"
        assert details["fund_house"] == expected["fund_house"], \
            f"Fund House mismatch for {code}: Expected '{expected['fund_house']}', Got '{details['fund_house']}'"


def test_decimal_precision_portfolio_metrics():
    """
    Regression Test: Verifies that Decimal calculations eliminate floating point precision drift
    in transaction units, invested amounts, and portfolio valuations.
    """
    transactions = [
        {
            "scheme_code": "122639",
            "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
            "transaction_type": "SIP",
            "transaction_date": "2025-08-14",
            "units": Decimal("108.420241"),
            "nav": Decimal("92.2337"),
            "amount": Decimal("10000.00")
        },
        {
            "scheme_code": "119063",
            "scheme_name": "HDFC Nifty 50 Index Fund - Direct Plan - Growth Option",
            "transaction_type": "SIP",
            "transaction_date": "2025-08-14",
            "units": Decimal("20.911499"),
            "nav": Decimal("239.1029"),
            "amount": Decimal("5000.00")
        }
    ]

    current_navs = {
        "122639": 90.4982,
        "119063": 236.4268
    }

    res = calculate_portfolio_metrics(transactions, current_navs)
    assert res["success"] is True

    # Validate exact fund-level rounded sum equals portfolio current value to 2 decimal places
    sum_rounded = round(sum(f["current_value"] for f in res["fund_breakdown"]), 2)
    assert res["current_value"] == sum_rounded, f"Mismatch: Portfolio Value ({res['current_value']}) != Sum of Funds ({sum_rounded})"

    # Validate exact total invested
    assert res["total_invested"] == 15000.0
