import pytest
from app.engines.risk import calculate_risk_metrics


def test_risk_metrics_calculation():
    # 20 days NAV sequence
    navs = [100.0 + (i * 0.5) for i in range(20)]
    res = calculate_risk_metrics(navs)

    assert res["success"] is True
    assert "volatility_annual_pct" in res
    assert "sharpe_ratio" in res
    assert "sortino_ratio" in res
    assert "max_drawdown_pct" in res


def test_risk_metrics_insufficient_data():
    res = calculate_risk_metrics([100.0, 101.0])
    assert res["success"] is False
    assert res["error_code"] == "INSUFFICIENT_DATA"
