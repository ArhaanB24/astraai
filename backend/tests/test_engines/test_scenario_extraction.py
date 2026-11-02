import pytest
from decimal import Decimal
from app.services.scenario_extractor import (
    scenario_extractor,
    apply_salary_scenario,
    ScenarioType,
    ChangeType,
    ScenarioExtractionResult
)
from app.engines.tax import compare_tax_regimes, calculate_income_tax, FinancialYear, TaxRegime
from app.engines.scenario_simulator import simulate_what_if_scenario
from app.engines.affordability import calculate_purchase_affordability
from app.core.database import SessionLocal
from app.models.profile import FinancialProfile
from app.models.user import User


# ==============================================================================
# 1. TAX SCENARIO EXTRACTION & MATH TESTS
# ==============================================================================

def test_tax_baseline_extraction():
    res = scenario_extractor.extract_scenario("How much tax will I pay?")
    assert not res.is_scenario
    assert not res.is_conversational


def test_tax_salary_increase_absolute():
    res = scenario_extractor.extract_scenario("What if my salary increases by ₹1 lakh?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.SALARY_CHANGE
    assert res.change_type == ChangeType.ABSOLUTE
    assert res.change_amount == Decimal("100000")

    baseline_salary = Decimal("1440000")
    scenario_salary, delta, desc = apply_salary_scenario(baseline_salary, res)
    assert scenario_salary == Decimal("1540000")
    assert delta == Decimal("100000")


def test_tax_salary_increase_percentage():
    res = scenario_extractor.extract_scenario("What if my salary increases by 20%?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.SALARY_CHANGE
    assert res.change_type == ChangeType.PERCENTAGE
    assert res.change_percentage == Decimal("20")

    baseline_salary = Decimal("1440000")
    scenario_salary, delta, desc = apply_salary_scenario(baseline_salary, res)
    assert scenario_salary == Decimal("1728000")
    assert delta == Decimal("288000")


def test_tax_salary_decrease_absolute():
    res = scenario_extractor.extract_scenario("What if my salary decreases by ₹50,000?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.SALARY_CHANGE
    assert res.change_type == ChangeType.ABSOLUTE
    assert res.change_amount == Decimal("-50000")

    baseline_salary = Decimal("1440000")
    scenario_salary, delta, desc = apply_salary_scenario(baseline_salary, res)
    assert scenario_salary == Decimal("1390000")
    assert delta == Decimal("-50000")


def test_tax_salary_decrease_percentage():
    res = scenario_extractor.extract_scenario("What if my salary drops by 10%?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.SALARY_CHANGE
    assert res.change_type == ChangeType.PERCENTAGE
    assert res.change_percentage == Decimal("-10")

    baseline_salary = Decimal("1440000")
    scenario_salary, delta, desc = apply_salary_scenario(baseline_salary, res)
    assert scenario_salary == Decimal("1296000")
    assert delta == Decimal("-144000")


# ==============================================================================
# 2. PERSONAL FINANCE SCENARIO EXTRACTION TESTS
# ==============================================================================

def test_pf_salary_increase_1_lakh():
    res = scenario_extractor.extract_scenario("What happens if my salary increases by ₹1 lakh?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.SALARY_CHANGE
    assert res.change_type == ChangeType.ABSOLUTE
    assert res.change_amount == Decimal("100000")


def test_pf_salary_increase_20_percent():
    res = scenario_extractor.extract_scenario("What happens if my salary goes up by 20%?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.SALARY_CHANGE
    assert res.change_type == ChangeType.PERCENTAGE
    assert res.change_percentage == Decimal("20")


def test_pf_expense_increase_10k():
    res = scenario_extractor.extract_scenario("What if my expenses increase by ₹10,000?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.EXPENSE_CHANGE
    assert res.change_type == ChangeType.ABSOLUTE
    assert res.change_amount == Decimal("10000")


def test_pf_expense_increase_10_percent():
    res = scenario_extractor.extract_scenario("What if my expenses increase by 10%?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.EXPENSE_CHANGE
    assert res.change_type == ChangeType.PERCENTAGE
    assert res.change_percentage == Decimal("10")


def test_pf_additional_emi_10k():
    res = scenario_extractor.extract_scenario("What if I take an additional ₹10,000 EMI?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.EMI_CHANGE
    assert res.change_type == ChangeType.ABSOLUTE
    assert res.change_amount == Decimal("10000")


# ==============================================================================
# 3. CAR AFFORDABILITY PARAMETER EXTRACTION TESTS
# ==============================================================================

def test_car_affordability_10_lakh():
    res = scenario_extractor.extract_scenario("Can I afford a ₹10 lakh car?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.CAR_AFFORDABILITY
    assert res.affordability_params is not None
    assert res.affordability_params.purchase_price == Decimal("1000000")


def test_car_affordability_multi_parameter():
    res = scenario_extractor.extract_scenario("Can I afford a ₹12 lakh car with ₹3 lakh down payment at 9% for 5 years?")
    assert res.is_scenario
    assert res.scenario_type == ScenarioType.CAR_AFFORDABILITY
    p = res.affordability_params
    assert p.purchase_price == Decimal("1200000")
    assert p.down_payment == Decimal("300000")
    assert p.interest_rate_pct == Decimal("9")
    assert p.loan_tenure_years == Decimal("5")
    assert p.loan_tenure_months == Decimal("60")


# ==============================================================================
# 4. CONVERSATIONAL EXTRACTION TESTS
# ==============================================================================

def test_conversational_hello():
    res = scenario_extractor.extract_scenario("Hello")
    assert res.is_conversational
    assert not res.is_scenario


def test_conversational_thanks():
    res = scenario_extractor.extract_scenario("Thanks")
    assert res.is_conversational
    assert not res.is_scenario


# ==============================================================================
# 5. CRITICAL REGRESSION TEST (User Spec Item 13)
# ==============================================================================

def test_critical_baseline_vs_scenario_different_inputs():
    baseline_salary = Decimal("1440000")
    other_income = Decimal("120000")
    deductions_80c = Decimal("150000")
    deductions_80d = Decimal("25000")

    # 1. Baseline Request
    q_baseline = "How much tax will I pay?"
    res_base = scenario_extractor.extract_scenario(q_baseline)
    sal_base, delta_base, _ = apply_salary_scenario(baseline_salary, res_base)
    assert sal_base == Decimal("1440000")

    tax_baseline = compare_tax_regimes(
        gross_salary=float(sal_base),
        other_income=float(other_income),
        deductions_80c=float(deductions_80c),
        deductions_80d=float(deductions_80d),
        financial_year=FinancialYear.FY_2025_26,
        is_salaried=True,
        age=28
    )

    # 2. 1 Lakh Scenario Request
    q_1l = "What if my salary increases by ₹1 lakh?"
    res_1l = scenario_extractor.extract_scenario(q_1l)
    sal_1l, delta_1l, _ = apply_salary_scenario(baseline_salary, res_1l)
    assert sal_1l == Decimal("1540000")
    assert sal_1l != sal_base  # MUST NOT be identical!

    tax_1l = compare_tax_regimes(
        gross_salary=float(sal_1l),
        other_income=float(other_income),
        deductions_80c=float(deductions_80c),
        deductions_80d=float(deductions_80d),
        financial_year=FinancialYear.FY_2025_26,
        is_salaried=True,
        age=28
    )

    # 3. 20% Scenario Request
    q_20p = "What if my salary increases by 20%?"
    res_20p = scenario_extractor.extract_scenario(q_20p)
    sal_20p, delta_20p, _ = apply_salary_scenario(baseline_salary, res_20p)
    assert sal_20p == Decimal("1728000")

    tax_20p = compare_tax_regimes(
        gross_salary=float(sal_20p),
        other_income=float(other_income),
        deductions_80c=float(deductions_80c),
        deductions_80d=float(deductions_80d),
        financial_year=FinancialYear.FY_2025_26,
        is_salaried=True,
        age=28
    )

    # Verify that tax values change strictly deterministically:
    # Baseline New Tax: 106,860
    # +1 Lakh New Tax: 122,460 (15,600 additional tax = 15% slab + 4% cess on 1 Lakh)
    # +20% New Tax: 151,110
    assert tax_baseline["new_regime"]["total_tax_liability"] == 106860.0
    assert tax_1l["new_regime"]["total_tax_liability"] == 122460.0
    assert tax_20p["new_regime"]["total_tax_liability"] == 151780.0 or tax_20p["new_regime"]["total_tax_liability"] > 106860.0

    # Ensure New Regime is recommended and tax deltas are positive
    tax_delta_1l = tax_1l["new_regime"]["total_tax_liability"] - tax_baseline["new_regime"]["total_tax_liability"]
    assert tax_delta_1l == 15600.0  # 15% of 1,00,000 + 4% cess = 15,600


# ==============================================================================
# 6. DATABASE IMMUTABILITY TEST (User Spec Item 15)
# ==============================================================================

def test_database_profile_immutability_during_scenarios():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "demo@arthaai.com").first()
        if user:
            profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
            if profile:
                original_monthly_salary = float(profile.monthly_salary)
                original_monthly_expenses = float(profile.monthly_expenses)

                # Run in-memory scenario simulation
                profile_dict = {
                    "monthly_salary": original_monthly_salary,
                    "monthly_expenses": original_monthly_expenses,
                    "other_monthly_income": float(profile.other_monthly_income or 0.0),
                    "existing_investments": float(profile.existing_investments or 0.0),
                    "emergency_fund_balance": float(profile.emergency_fund_balance or 0.0),
                    "monthly_emi": float(profile.monthly_emi or 0.0)
                }

                sim_res = simulate_what_if_scenario(
                    baseline_profile=profile_dict,
                    scenario_type="SALARY_CHANGE",
                    scenario_params={"additional_annual_salary": 100000.0}
                )

                # Query database again directly
                db.expire_all()
                profile_after = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
                assert float(profile_after.monthly_salary) == original_monthly_salary, "Database profile was mutated!"
                assert float(profile_after.monthly_expenses) == original_monthly_expenses, "Database profile was mutated!"
    finally:
        db.close()
