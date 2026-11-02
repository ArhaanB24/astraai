from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
from app.engines.emi import calculate_emi_and_amortization


def _to_dec(val: Any) -> Decimal:
    if val is None:
        return Decimal("0.0")
    return Decimal(str(val))


def _round_dec(val: Decimal, places: int = 2) -> float:
    fmt = "0." + "0" * places if places > 0 else "0"
    return float(val.quantize(Decimal(fmt), rounding=ROUND_HALF_UP))


def calculate_purchase_affordability(
    purchase_price: float,
    down_payment: float,
    loan_interest_rate_pct: float,
    loan_tenure_years: float,
    monthly_income: float,
    monthly_expenses: float,
    existing_emis: float = 0.0,
    emergency_fund_balance: float = 0.0,
    monthly_sip: float = 0.0,
    goals: List[Dict[str, Any]] = None,
    draw_down_payment_from_emergency: bool = True
) -> Dict[str, Any]:
    """
    Deterministically computes purchase affordability (e.g. Car or Home purchase)
    using strict Decimal arithmetic.

    Inputs:
    - purchase_price: e.g. ₹15,00,000
    - down_payment: e.g. ₹3,00,000
    - loan_interest_rate_pct: e.g. 8.5%
    - loan_tenure_years: e.g. 5.0 years (60 months)
    """
    if purchase_price <= 0:
        raise ValueError("Car purchase price must be greater than 0.")
    if down_payment > purchase_price:
        raise ValueError("Down payment cannot exceed purchase price.")

    price_dec = _to_dec(purchase_price)
    down_payment_dec = max(Decimal("0.0"), _to_dec(down_payment))
    rate_pct_dec = max(Decimal("0.0"), _to_dec(loan_interest_rate_pct))
    tenure_months = int(max(Decimal("0.0"), _to_dec(loan_tenure_years)) * Decimal("12.0"))

    income_dec = max(Decimal("0.0"), _to_dec(monthly_income))
    expenses_dec = max(Decimal("0.0"), _to_dec(monthly_expenses))
    existing_emis_dec = max(Decimal("0.0"), _to_dec(existing_emis))
    emergency_bal_dec = max(Decimal("0.0"), _to_dec(emergency_fund_balance))
    sip_dec = max(Decimal("0.0"), _to_dec(monthly_sip))

    loan_amount_dec = price_dec - down_payment_dec
    if loan_amount_dec < Decimal("0.0"):
        loan_amount_dec = Decimal("0.0")

    # Calculate exact EMI
    if loan_amount_dec == Decimal("0.0"):
        emi_result = {
            "monthly_emi": 0.0,
            "total_interest": 0.0,
            "total_payment": 0.0
        }
    else:
        emi_result = calculate_emi_and_amortization(
            principal=float(loan_amount_dec),
            annual_interest_rate_pct=float(rate_pct_dec),
            tenure_months=tenure_months,
            generate_schedule=False
        )

    new_emi_dec = _to_dec(emi_result["monthly_emi"])
    total_interest_dec = _to_dec(emi_result["total_interest"])
    total_loan_payment_dec = _to_dec(emi_result["total_payment"])

    # Cash Flows
    total_new_emis_dec = existing_emis_dec + new_emi_dec
    total_outflow_dec = expenses_dec + total_new_emis_dec
    remaining_surplus_dec = income_dec - total_outflow_dec
    baseline_surplus_dec = income_dec - (expenses_dec + existing_emis_dec)

    # Ratios
    if income_dec > Decimal("0.0"):
        new_dti_pct_dec = (total_new_emis_dec / income_dec) * Decimal("100.0")
        emi_to_income_pct_dec = (new_emi_dec / income_dec) * Decimal("100.0")
        new_savings_rate_pct_dec = ((remaining_surplus_dec + sip_dec) / income_dec) * Decimal("100.0")
    else:
        new_dti_pct_dec = Decimal("0.0")
        emi_to_income_pct_dec = Decimal("0.0")
        new_savings_rate_pct_dec = Decimal("0.0")

    # Emergency Fund Impact Trace
    if draw_down_payment_from_emergency:
        post_emergency_bal_dec = emergency_bal_dec - down_payment_dec
        if post_emergency_bal_dec < Decimal("0.0"):
            post_emergency_bal_dec = Decimal("0.0")
    else:
        post_emergency_bal_dec = emergency_bal_dec

    if expenses_dec > Decimal("0.0"):
        post_emergency_coverage_months_dec = post_emergency_bal_dec / expenses_dec
        baseline_emergency_coverage_months_dec = emergency_bal_dec / expenses_dec
    else:
        post_emergency_coverage_months_dec = Decimal("0.0")
        baseline_emergency_coverage_months_dec = Decimal("0.0")

    # Active Goals Impact Evaluation
    total_required_goal_sip_dec = Decimal("0.0")
    if goals:
        for g in goals:
            total_required_goal_sip_dec += _to_dec(g.get("required_monthly_contribution", 0.0))

    goal_surplus_gap_dec = remaining_surplus_dec - total_required_goal_sip_dec
    goals_impacted = goal_surplus_gap_dec < Decimal("0.0")

    # Risk Flags
    risk_flags = []
    if remaining_surplus_dec < Decimal("0.0"):
        risk_flags.append("Monthly cash outflow exceeds monthly income (Deficit Budget)")
    if new_dti_pct_dec > Decimal("50.0"):
        risk_flags.append(f"Total Debt-to-Income ratio is dangerously high ({new_dti_pct_dec:.1f}%)")
    elif emi_to_income_pct_dec > Decimal("25.0"):
        risk_flags.append(f"New loan EMI alone consumes {emi_to_income_pct_dec:.1f}% of your monthly income")

    if post_emergency_coverage_months_dec < Decimal("3.0"):
        risk_flags.append(f"Emergency fund reduced to {post_emergency_coverage_months_dec:.1f} months of expenses (below 3-month safety threshold)")

    if goals_impacted:
        risk_flags.append(f"Post-purchase monthly surplus is insufficient to fund your active financial goals (Gap: ₹{abs(goal_surplus_gap_dec):,.2f}/mo)")

    # Rating
    if remaining_surplus_dec <= Decimal("0.0") or new_dti_pct_dec > Decimal("55.0"):
        assessment = "UNAFFORDABLE"
    elif new_dti_pct_dec > Decimal("45.0") or post_emergency_coverage_months_dec < Decimal("3.0") or goals_impacted:
        assessment = "STRETCHED"
    elif new_dti_pct_dec > Decimal("35.0") or post_emergency_coverage_months_dec < Decimal("6.0"):
        assessment = "MODERATELY_AFFORDABLE"
    else:
        assessment = "HIGHLY_AFFORDABLE"

    return {
        "purchase_price": _round_dec(price_dec, 2),
        "down_payment": _round_dec(down_payment_dec, 2),
        "loan_amount": _round_dec(loan_amount_dec, 2),
        "loan_interest_rate_pct": loan_interest_rate_pct,
        "loan_tenure_years": loan_tenure_years,
        "loan_tenure_months": tenure_months,
        "new_monthly_emi": _round_dec(new_emi_dec, 2),
        "total_loan_interest": _round_dec(total_interest_dec, 2),
        "total_loan_payment": _round_dec(total_loan_payment_dec, 2),
        "baseline_monthly_surplus": _round_dec(baseline_surplus_dec, 2),
        "post_purchase_monthly_surplus": _round_dec(remaining_surplus_dec, 2),
        "new_debt_to_income_pct": _round_dec(new_dti_pct_dec, 2),
        "emi_to_income_pct": _round_dec(emi_to_income_pct_dec, 2),
        "new_savings_rate_pct": _round_dec(new_savings_rate_pct_dec, 2),
        "pre_purchase_liquid_assets": _round_dec(emergency_bal_dec, 2),
        "baseline_emergency_coverage_months": _round_dec(baseline_emergency_coverage_months_dec, 2),
        "post_purchase_emergency_coverage_months": _round_dec(post_emergency_coverage_months_dec, 2),
        "emergency_fund_balance_after_down_payment": _round_dec(post_emergency_bal_dec, 2),
        "draw_down_payment_from_emergency": draw_down_payment_from_emergency,
        "total_required_goal_monthly_contribution": _round_dec(total_required_goal_sip_dec, 2),
        "goal_surplus_gap": _round_dec(goal_surplus_gap_dec, 2),
        "goals_impacted": goals_impacted,
        "affordability_assessment": assessment,
        "risk_flags": risk_flags
    }
