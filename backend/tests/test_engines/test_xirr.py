import pytest
from datetime import datetime, timedelta
from app.engines.xirr import calculate_xirr


def test_xirr_simple_annual_return():
    """Test 10% annual return cash flow over 1 year."""
    dates = [datetime(2023, 1, 1), datetime(2024, 1, 1)]
    cash_flows = [
        (dates[0], -10000.0),
        (dates[1], 11000.0)
    ]
    res = calculate_xirr(cash_flows)
    assert res["success"] is True
    assert pytest.approx(res["xirr_percentage"], 0.5) == 10.0


def test_xirr_monthly_sip_cash_flows():
    """Test 12-month SIP of ₹5000 with positive final valuation."""
    cash_flows = []
    base_date = datetime(2023, 1, 1)
    for m in range(12):
        cf_date = base_date + timedelta(days=30 * m)
        cash_flows.append((cf_date, -5000.0))

    # Total invested = ₹60,000, current valuation = ₹65,000
    cash_flows.append((base_date + timedelta(days=365), 65000.0))

    res = calculate_xirr(cash_flows)
    assert res["success"] is True
    assert res["xirr_percentage"] > 0.0


def test_xirr_negative_return():
    """Test investment with loss."""
    cash_flows = [
        (datetime(2023, 1, 1), -10000.0),
        (datetime(2024, 1, 1), 8000.0)
    ]
    res = calculate_xirr(cash_flows)
    assert res["success"] is True
    assert res["xirr_percentage"] < 0.0


def test_xirr_insufficient_data():
    """Test error handling when less than 2 cash flows provided."""
    res = calculate_xirr([(datetime(2023, 1, 1), -10000.0)])
    assert res["success"] is False
    assert res["error_code"] == "INSUFFICIENT_DATA"


def test_xirr_invalid_cash_flows():
    """Test error handling when all cash flows are positive or all negative."""
    cash_flows = [
        (datetime(2023, 1, 1), -10000.0),
        (datetime(2023, 6, 1), -5000.0)
    ]
    res = calculate_xirr(cash_flows)
    assert res["success"] is False
    assert res["error_code"] == "INVALID_CASH_FLOWS"
