from typing import Dict, Any


def calculate_sip_future_value(monthly_investment: float, expected_annual_return_pct: float, tenure_years: int) -> Dict[str, Any]:
    """
    Calculates future value and wealth gain for a monthly Systematic Investment Plan (SIP).
    Formula: FV = P * [((1 + i)^n - 1) / i] * (1 + i)
    where:
    P = monthly investment
    i = monthly interest rate (annual rate / 12 / 100)
    n = total months (tenure_years * 12)
    """
    if monthly_investment <= 0:
        return {
            "success": False,
            "error_code": "INVALID_AMOUNT",
            "message": "Monthly investment amount must be greater than zero."
        }
    if tenure_years <= 0:
        return {
            "success": False,
            "error_code": "INVALID_TENURE",
            "message": "Tenure years must be greater than zero."
        }

    n = tenure_years * 12
    i = expected_annual_return_pct / 100.0 / 12.0

    if i == 0:
        future_value = monthly_investment * n
    else:
        future_value = monthly_investment * (((1 + i) ** n - 1) / i) * (1 + i)

    total_invested = monthly_investment * n
    estimated_returns = future_value - total_invested

    return {
        "success": True,
        "monthly_investment": float(monthly_investment),
        "tenure_years": int(tenure_years),
        "total_months": int(n),
        "expected_annual_return_pct": float(expected_annual_return_pct),
        "total_invested": round(float(total_invested), 2),
        "estimated_returns": round(float(estimated_returns), 2),
        "future_value": round(float(future_value), 2)
    }
