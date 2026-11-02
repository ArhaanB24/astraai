from datetime import datetime
from typing import List, Dict, Any, Tuple, Union
import numpy as np
from scipy.optimize import newton, brentq


def _xnpv(rate: float, dates: List[datetime], amounts: List[float]) -> float:
    """Calculate Net Present Value for irregular cash flows given annual rate."""
    if rate <= -1.0:
        return float('inf')
    t0 = dates[0]
    return sum(
        amount / ((1.0 + rate) ** ((d - t0).days / 365.25))
        for d, amount in zip(dates, amounts)
    )


def _xnpv_derivative(rate: float, dates: List[datetime], amounts: List[float]) -> float:
    """Derivative of XNPV with respect to rate for Newton-Raphson."""
    if rate <= -1.0:
        return float('inf')
    t0 = dates[0]
    return sum(
        -((d - t0).days / 365.25) * amount / ((1.0 + rate) ** (((d - t0).days / 365.25) + 1.0))
        for d, amount in zip(dates, amounts)
    )


def calculate_xirr(cash_flows: List[Tuple[datetime, float]]) -> Dict[str, Any]:
    """
    Calculates exact XIRR using a two-stage solver:
    1. Newton-Raphson algorithm with analytical derivative.
    2. Bracketing / Brent fallback algorithm if Newton-Raphson fails to converge.
    3. Structured error return if cash flows are invalid or no convergence exists.

    Cash flow format: List of (date, amount) tuples.
    Outflows (investments/SIPs) should be NEGATIVE (e.g. -5000).
    Inflows (current portfolio value / withdrawals) should be POSITIVE (e.g. +15000).
    """
    if not cash_flows or len(cash_flows) < 2:
        return {
            "success": False,
            "error_code": "INSUFFICIENT_DATA",
            "message": "At least two cash flows (one investment, one current value) are required to compute XIRR.",
            "missing_fields": ["cash_flows"]
        }

    # Sort cash flows by date
    sorted_cf = sorted(cash_flows, key=lambda x: x[0])
    dates = [cf[0] for cf in sorted_cf]
    amounts = [float(cf[1]) for cf in sorted_cf]

    has_negative = any(a < 0 for a in amounts)
    has_positive = any(a > 0 for a in amounts)

    if not (has_negative and has_positive):
        return {
            "success": False,
            "error_code": "INVALID_CASH_FLOWS",
            "message": "Cash flows must contain at least one negative flow (investment) and one positive flow (current value/redemption)."
        }

    # Stage 1: Try Newton-Raphson solver
    try:
        rate = newton(
            func=lambda r: _xnpv(r, dates, amounts),
            x0=0.1,
            fprime=lambda r: _xnpv_derivative(r, dates, amounts),
            maxiter=100,
            tol=1e-6
        )
        if not np.isnan(rate) and not np.isinf(rate) and rate > -1.0:
            return {
                "success": True,
                "xirr_percentage": round(float(rate * 100.0), 2),
                "xirr_decimal": float(rate),
                "method": "newton-raphson"
            }
    except (RuntimeError, OverflowError, ZeroDivisionError):
        pass

    # Stage 2: Fallback to Brent / Bracketing solver
    try:
        # Search for sign change in rate interval [-0.99, 10.0]
        a_val, b_val = -0.99, 10.0
        fa = _xnpv(a_val, dates, amounts)
        fb = _xnpv(b_val, dates, amounts)

        if fa * fb < 0:
            rate = brentq(lambda r: _xnpv(r, dates, amounts), a_val, b_val, xtol=1e-6)
            return {
                "success": True,
                "xirr_percentage": round(float(rate * 100.0), 2),
                "xirr_decimal": float(rate),
                "method": "brent"
            }
    except Exception:
        pass

    # Stage 3: Explicit Failure Return (LLM NEVER guesses XIRR)
    return {
        "success": False,
        "error_code": "XIRR_NO_CONVERGENCE",
        "message": "XIRR calculation did not converge for the supplied irregular cash flows."
    }
