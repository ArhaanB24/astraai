from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List


def _to_dec(val: Any) -> Decimal:
    if val is None:
        return Decimal("0.0")
    return Decimal(str(val))


def _round_dec(val: Decimal, places: int = 2) -> float:
    fmt = "0." + "0" * places if places > 0 else "0"
    return float(val.quantize(Decimal(fmt), rounding=ROUND_HALF_UP))


def calculate_emi_and_amortization(
    principal: float,
    annual_interest_rate_pct: float,
    tenure_months: int,
    generate_schedule: bool = True
) -> Dict[str, Any]:
    """
    Computes exact monthly EMI, total interest, total payment, and month-by-month
    amortization schedule using strict Decimal arithmetic.

    Edge Cases Handled:
    - Principal <= 0
    - Tenure <= 0
    - 0% Interest Rate
    - Negative Interest Rates (Clamped to 0.0)
    - Schedule reconciliation: final closing balance == 0.00
    """
    p_dec = max(Decimal("0.0"), _to_dec(principal))
    rate_annual_dec = max(Decimal("0.0"), _to_dec(annual_interest_rate_pct)) / Decimal("100.0")
    r_monthly_dec = rate_annual_dec / Decimal("12.0")
    n = max(1, tenure_months) if p_dec > Decimal("0.0") else 0

    if p_dec <= Decimal("0.0") or n == 0:
        return {
            "principal": 0.0,
            "annual_interest_rate_pct": float(rate_annual_dec * Decimal("100.0")),
            "tenure_months": tenure_months,
            "monthly_emi": 0.0,
            "total_interest": 0.0,
            "total_payment": 0.0,
            "amortization_schedule": []
        }

    if r_monthly_dec > Decimal("0.0"):
        factor = (Decimal("1.0") + r_monthly_dec) ** Decimal(str(n))
        emi_dec = (p_dec * r_monthly_dec * factor) / (factor - Decimal("1.0"))
    else:
        emi_dec = p_dec / Decimal(str(n))

    emi_rounded_dec = emi_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    schedule: List[Dict[str, Any]] = []
    total_interest_paid_dec = Decimal("0.0")
    total_principal_paid_dec = Decimal("0.0")

    if generate_schedule:
        balance_dec = p_dec
        for m in range(1, n + 1):
            opening_bal_dec = balance_dec
            interest_m_dec = (balance_dec * r_monthly_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            principal_m_dec = emi_rounded_dec - interest_m_dec
            if m == n or principal_m_dec > balance_dec:
                principal_m_dec = balance_dec
                emi_this_month_dec = principal_m_dec + interest_m_dec
            else:
                emi_this_month_dec = emi_rounded_dec

            balance_dec -= principal_m_dec
            if balance_dec < Decimal("0.0"):
                balance_dec = Decimal("0.0")

            total_interest_paid_dec += interest_m_dec
            total_principal_paid_dec += principal_m_dec

            schedule.append({
                "month": m,
                "opening_balance": _round_dec(opening_bal_dec, 2),
                "emi": _round_dec(emi_this_month_dec, 2),
                "principal_component": _round_dec(principal_m_dec, 2),
                "interest_component": _round_dec(interest_m_dec, 2),
                "closing_balance": _round_dec(balance_dec, 2),
                "remaining_principal": _round_dec(balance_dec, 2)
            })

        total_payment_dec = total_principal_paid_dec + total_interest_paid_dec
        total_interest_dec = total_interest_paid_dec
    else:
        total_payment_dec = emi_rounded_dec * Decimal(str(n))
        total_interest_dec = total_payment_dec - p_dec

    return {
        "principal": _round_dec(p_dec, 2),
        "annual_interest_rate_pct": float(rate_annual_dec * Decimal("100.0")),
        "tenure_months": n,
        "tenure_years": _round_dec(Decimal(str(n)) / Decimal("12.0"), 1),
        "monthly_emi": _round_dec(emi_rounded_dec, 2),
        "total_interest": _round_dec(total_interest_dec, 2),
        "total_payment": _round_dec(total_payment_dec, 2),
        "amortization_schedule": schedule
    }
