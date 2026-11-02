from typing import List, Dict, Any
import numpy as np


def calculate_risk_metrics(
    daily_navs: List[float],
    benchmark_daily_navs: List[float] = None,
    risk_free_rate_annual: float = 6.5
) -> Dict[str, Any]:
    """
    Computes deterministic risk metrics for a mutual fund:
    - Volatility (Annualized standard deviation of daily returns)
    - Sharpe Ratio = (Annualized Return - Risk Free Rate) / Annualized Volatility
    - Sortino Ratio = (Annualized Return - Risk Free Rate) / Downside Deviation
    - Maximum Drawdown = Max peak-to-trough decline percentage
    - Beta (Covariance with benchmark / Benchmark Variance)
    """
    if not daily_navs or len(daily_navs) < 10:
        return {
            "success": False,
            "error_code": "INSUFFICIENT_DATA",
            "message": "At least 10 historical NAV entries are required to compute risk metrics."
        }

    navs = np.array(daily_navs, dtype=float)
    # Calculate daily percentage returns
    returns = np.diff(navs) / navs[:-1]

    if len(returns) == 0:
        return {"success": False, "error_code": "INVALID_DATA", "message": "Could not calculate returns from NAV history."}

    # Annualized Volatility
    daily_vol = np.std(returns, ddof=1)
    annual_vol = daily_vol * np.sqrt(252)

    # Annualized Mean Return
    mean_daily = np.mean(returns)
    annual_return = mean_daily * 252

    rf_decimal = risk_free_rate_annual / 100.0

    # Sharpe Ratio
    sharpe = (annual_return - rf_decimal) / annual_vol if annual_vol > 0 else 0.0

    # Downside Deviation for Sortino
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 0:
        downside_std = np.std(downside_returns, ddof=1) * np.sqrt(252)
        sortino = (annual_return - rf_decimal) / downside_std if downside_std > 0 else 0.0
    else:
        sortino = sharpe * 1.5

    # Maximum Drawdown
    cumulative = np.maximum.accumulate(navs)
    drawdowns = (navs - cumulative) / cumulative
    max_drawdown = float(np.min(drawdowns)) * 100.0  # as percentage

    # Beta
    beta = 1.0
    if benchmark_daily_navs and len(benchmark_daily_navs) == len(daily_navs):
        bench_navs = np.array(benchmark_daily_navs, dtype=float)
        bench_returns = np.diff(bench_navs) / bench_navs[:-1]
        cov = np.cov(returns, bench_returns)[0][1]
        bench_var = np.var(bench_returns, ddof=1)
        if bench_var > 0:
            beta = cov / bench_var

    return {
        "success": True,
        "volatility_annual_pct": round(float(annual_vol * 100.0), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "sortino_ratio": round(float(sortino), 2),
        "max_drawdown_pct": round(float(max_drawdown), 2),
        "beta": round(float(beta), 2),
        "annualized_return_pct": round(float(annual_return * 100.0), 2)
    }
