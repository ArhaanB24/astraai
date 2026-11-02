import pytest
from app.engines.cagr import calculate_cagr


def test_cagr_positive():
    # 100 to 121 in 2 years = 10% CAGR
    res = calculate_cagr(100.0, 121.0, 2.0)
    assert res["success"] is True
    assert res["cagr_percentage"] == 10.0


def test_cagr_invalid_initial():
    res = calculate_cagr(0.0, 100.0, 2.0)
    assert res["success"] is False
    assert res["error_code"] == "INVALID_AMOUNT"
