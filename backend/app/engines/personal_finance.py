from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List


def _to_dec(val: Any) -> Decimal:
    if val is None:
        return Decimal("0.0")
    return Decimal(str(val))


def _round_dec(val: Decimal, places: int = 2) -> float:
    fmt = "0." + "0" * places if places > 0 else "0"
    return float(val.quantize(Decimal(fmt), rounding=ROUND_HALF_UP))


def calculate_financial_health(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministically computes financial health metrics using strict Decimal arithmetic.

    Formulas:
    - monthly_income = sum(income_sources) OR (monthly_salary + other_monthly_income)
    - monthly_expenses = sum(expense_items) OR monthly_expenses
    - monthly_emis = sum(liability_emis) OR monthly_emi
    - monthly_surplus = monthly_income - monthly_expenses - monthly_emis
    - savings_rate = (monthly_surplus + monthly_sip) / monthly_income * 100
    - debt_to_income = (monthly_emis / monthly_income) * 100
    - net_worth = total_assets - total_liabilities
    - emergency_coverage = emergency_fund_balance / monthly_expenses
    """
    salary = _to_dec(profile_data.get("monthly_salary", 0.0))
    other_income = _to_dec(profile_data.get("other_monthly_income", 0.0))
    income_sources = profile_data.get("income_sources", [])

    if income_sources:
        total_income_dec = sum([_to_dec(i.get("amount", 0.0)) for i in income_sources], Decimal("0.0"))
    else:
        total_income_dec = salary + other_income

    expenses = _to_dec(profile_data.get("monthly_expenses", 0.0))
    expense_items = profile_data.get("expense_items", [])

    if expense_items:
        total_expenses_dec = sum([_to_dec(e.get("amount", 0.0)) for e in expense_items if e.get("category") != "EMI"], Decimal("0.0"))
    else:
        total_expenses_dec = expenses

    monthly_emi = _to_dec(profile_data.get("monthly_emi", 0.0))
    liability_items = profile_data.get("liability_items", [])

    if liability_items:
        total_emi_dec = sum([_to_dec(l.get("monthly_emi", 0.0)) for l in liability_items], Decimal("0.0"))
        total_liabilities_dec = sum([_to_dec(l.get("principal_outstanding", 0.0)) for l in liability_items], Decimal("0.0"))
    else:
        total_emi_dec = monthly_emi
        total_liabilities_dec = total_emi_dec * Decimal("36.0")

    total_outflow_dec = total_expenses_dec + total_emi_dec
    monthly_surplus_dec = total_income_dec - total_outflow_dec

    monthly_sip_dec = _to_dec(profile_data.get("monthly_sip", 0.0))

    if total_income_dec > Decimal("0.0"):
        savings_rate_pct_dec = ((monthly_surplus_dec + monthly_sip_dec) / total_income_dec) * Decimal("100.0")
        dti_pct_dec = (total_emi_dec / total_income_dec) * Decimal("100.0")
    else:
        savings_rate_pct_dec = Decimal("0.0")
        dti_pct_dec = Decimal("0.0")

    bank_balance = _to_dec(profile_data.get("bank_balance", 0.0))
    existing_investments = _to_dec(profile_data.get("existing_investments", 0.0))
    asset_items = profile_data.get("asset_items", [])

    if asset_items:
        total_assets_dec = sum([_to_dec(a.get("amount", 0.0)) for a in asset_items], Decimal("0.0"))
    else:
        total_assets_dec = bank_balance + existing_investments

    net_worth_dec = total_assets_dec - total_liabilities_dec

    emergency_fund_dec = _to_dec(profile_data.get("emergency_fund_balance", bank_balance))
    target_months = int(profile_data.get("target_emergency_months", 6))

    if total_expenses_dec > Decimal("0.0"):
        emergency_coverage_months_dec = emergency_fund_dec / total_expenses_dec
    else:
        emergency_coverage_months_dec = Decimal("0.0")

    # Deterministic Health Score (0 - 100)
    score = Decimal("0.0")

    # 1. Savings Rate Score (Max 30 pts)
    if savings_rate_pct_dec >= Decimal("30.0"):
        score += Decimal("30.0")
    elif savings_rate_pct_dec >= Decimal("20.0"):
        score += Decimal("22.0")
    elif savings_rate_pct_dec >= Decimal("10.0"):
        score += Decimal("14.0")
    elif savings_rate_pct_dec > Decimal("0.0"):
        score += Decimal("7.0")

    # 2. DTI Debt Score (Max 25 pts)
    if dti_pct_dec <= Decimal("20.0"):
        score += Decimal("25.0")
    elif dti_pct_dec <= Decimal("35.0"):
        score += Decimal("18.0")
    elif dti_pct_dec <= Decimal("50.0"):
        score += Decimal("10.0")
    else:
        score += Decimal("3.0")

    # 3. Emergency Coverage Score (Max 25 pts)
    if emergency_coverage_months_dec >= Decimal(str(target_months)):
        score += Decimal("25.0")
    elif emergency_coverage_months_dec >= Decimal("3.0"):
        score += Decimal("17.0")
    elif emergency_coverage_months_dec >= Decimal("1.0"):
        score += Decimal("9.0")

    # 4. Net Worth Score (Max 20 pts)
    if net_worth_dec > Decimal("0.0"):
        score += Decimal("20.0")
    elif net_worth_dec == Decimal("0.0"):
        score += Decimal("10.0")

    health_status = (
        "EXCELLENT" if score >= Decimal("80") else
        "GOOD" if score >= Decimal("65") else
        "FAIR" if score >= Decimal("50") else
        "NEEDS_ATTENTION"
    )

    return {
        "monthly_income": _round_dec(total_income_dec, 2),
        "monthly_expenses": _round_dec(total_expenses_dec, 2),
        "monthly_emis": _round_dec(total_emi_dec, 2),
        "total_monthly_outflow": _round_dec(total_outflow_dec, 2),
        "monthly_surplus": _round_dec(monthly_surplus_dec, 2),
        "savings_rate_pct": _round_dec(savings_rate_pct_dec, 2),
        "debt_to_income_pct": _round_dec(dti_pct_dec, 2),
        "total_assets": _round_dec(total_assets_dec, 2),
        "total_liabilities": _round_dec(total_liabilities_dec, 2),
        "net_worth": _round_dec(net_worth_dec, 2),
        "emergency_fund_balance": _round_dec(emergency_fund_dec, 2),
        "emergency_coverage_months": _round_dec(emergency_coverage_months_dec, 2),
        "target_emergency_months": target_months,
        "health_score": int(_round_dec(score, 0)),
        "health_status": health_status
    }


def calculate_goal_required_sip(
    target_amount: float,
    current_amount: float,
    target_year: int,
    expected_return_pct: float = 10.0,
    current_year: int = 2026
) -> Dict[str, Any]:
    """
    Calculates required monthly contribution for a financial goal using PMT compounding math.
    Formula: Target_FV = Current_PV*(1+r)^n + PMT * [((1+r)^n - 1) / r]
    Handles edge cases: zero interest, completed goal, past target year.
    """
    target_dec = _to_dec(target_amount)
    current_dec = _to_dec(current_amount)

    if current_dec >= target_dec:
        return {
            "target_amount": _round_dec(target_dec, 2),
            "current_amount": _round_dec(current_dec, 2),
            "target_year": target_year,
            "investment_horizon_years": max(0, target_year - current_year),
            "expected_return_pct": expected_return_pct,
            "future_val_current_savings": _round_dec(current_dec, 2),
            "required_monthly_contribution": 0.0,
            "status": "COMPLETED_ON_TRACK"
        }

    if target_year <= current_year:
        remaining_dec = target_dec - current_dec
        return {
            "target_amount": _round_dec(target_dec, 2),
            "current_amount": _round_dec(current_dec, 2),
            "target_year": target_year,
            "investment_horizon_years": 0,
            "expected_return_pct": expected_return_pct,
            "future_val_current_savings": _round_dec(current_dec, 2),
            "required_monthly_contribution": _round_dec(remaining_dec, 2),
            "status": "PAST_DUE"
        }

    years = target_year - current_year
    months = years * 12

    r_annual_dec = _to_dec(expected_return_pct) / Decimal("100.0")
    r_monthly_dec = r_annual_dec / Decimal("12.0")

    if r_monthly_dec <= Decimal("0.0"):
        # Zero interest case
        fv_current_dec = current_dec
        remaining_target_dec = target_dec - fv_current_dec
        required_monthly_dec = remaining_target_dec / Decimal(str(months))
    else:
        # Standard PMT compounding formula
        fv_current_dec = current_dec * ((Decimal("1.0") + r_monthly_dec) ** Decimal(str(months)))
        remaining_target_dec = target_dec - fv_current_dec
        if remaining_target_dec <= Decimal("0.0"):
            required_monthly_dec = Decimal("0.0")
        else:
            comp_factor = ((Decimal("1.0") + r_monthly_dec) ** Decimal(str(months))) - Decimal("1.0")
            required_monthly_dec = remaining_target_dec * (r_monthly_dec / comp_factor)

    return {
        "target_amount": _round_dec(target_dec, 2),
        "current_amount": _round_dec(current_dec, 2),
        "target_year": target_year,
        "investment_horizon_years": years,
        "expected_return_pct": expected_return_pct,
        "future_val_current_savings": _round_dec(fv_current_dec, 2),
        "required_monthly_contribution": _round_dec(required_monthly_dec, 2),
        "status": "REQUIRES_CONTRIBUTION" if required_monthly_dec > Decimal("0.0") else "ON_TRACK"
    }
