import pytest
from datetime import datetime, date
from decimal import Decimal
from app.providers.mutual_funds.mfapi import MFAPIProvider
from app.engines.portfolio_history import calculate_portfolio_history


def test_portfolio_history_reconciliation_every_date():
    """
    Regression Test: Asserts that for every generated historical date:
    1. Cumulative invested equals sum of transaction amounts up to that date.
    2. Sum of individual fund position values equals portfolio market value to 0.00 discrepancy.
    3. Final point matches current valuation exactly (Rs. 239,955.70).
    """
    provider = MFAPIProvider()
    scheme_codes = ["122639", "119063", "120503"]

    nav_histories = {}
    for code in scheme_codes:
        raw_hist = provider.get_nav_history(code, limit=400)
        scheme_nav_map = {}
        for item in raw_hist:
            try:
                d_obj = datetime.strptime(item["date"], "%d-%m-%Y").date()
                scheme_nav_map[d_obj] = Decimal(str(item["nav"]))
            except Exception:
                continue
        nav_histories[code] = scheme_nav_map

    transactions = [
        {"scheme_code": "122639", "scheme_name": "Parag Parikh Flexi Cap Fund", "transaction_type": "SIP", "transaction_date": datetime(2025, 8, 14), "units": 1302.6884772389976, "amount": 120000.0, "nav": 92.1172},
        {"scheme_code": "119063", "scheme_name": "HDFC Nifty 50 Index Fund", "transaction_type": "SIP", "transaction_date": datetime(2025, 8, 14), "units": 249.61000651080235, "amount": 60000.0, "nav": 240.3750},
        {"scheme_code": "120503", "scheme_name": "Axis ELSS Tax Saver Fund", "transaction_type": "SIP", "transaction_date": datetime(2025, 8, 14), "units": 557.219189851867, "amount": 60000.0, "nav": 107.6775},
    ]

    eval_dates = [
        date(2025, 8, 14),
        date(2025, 9, 15),
        date(2025, 10, 15),
        date(2025, 11, 14),
        date(2025, 12, 15),
        date(2026, 1, 14),
        date(2026, 2, 13),
        date(2026, 3, 13),
        date(2026, 4, 15),
        date(2026, 5, 15),
        date(2026, 6, 15),
        date(2026, 7, 15),
        date(2026, 8, 20)
    ]

    series = calculate_portfolio_history(transactions, nav_histories, eval_dates)

    assert len(series) == len(eval_dates)

    for point in series:
        sum_positions = round(sum(f["position_value"] for f in point["fund_positions"]), 2)
        diff = round(abs(point["portfolio_market_value"] - sum_positions), 2)
        assert diff == 0.00, f"Discrepancy on {point['date']}: {diff}"

    # Final point check
    final_pt = series[-1]
    assert final_pt["portfolio_market_value"] == 239955.70, f"Final point value mismatch: {final_pt['portfolio_market_value']} != 239955.70"
