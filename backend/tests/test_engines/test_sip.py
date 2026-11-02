import pytest
from app.engines.sip import calculate_sip_future_value


def test_sip_future_value():
    # ₹5000 monthly, 12% expected annual return, 1 year
    res = calculate_sip_future_value(5000.0, 12.0, 1)
    assert res["success"] is True
    assert res["total_invested"] == 60000.0
    assert res["future_value"] > 60000.0


def test_sip_zero_investment():
    res = calculate_sip_future_value(0.0, 12.0, 1)
    assert res["success"] is False
    assert res["error_code"] == "INVALID_AMOUNT"
