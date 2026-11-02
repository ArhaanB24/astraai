import pytest
from app.engines.personal_finance import calculate_financial_health, calculate_goal_required_sip
from app.engines.emi import calculate_emi_and_amortization
from app.engines.affordability import calculate_purchase_affordability
from app.engines.scenario_simulator import simulate_what_if_scenario


def test_canonical_demo_profile_financial_health_reconciliation():
    """
    Exact Reconciliation Test for Alex Sharma's Canonical Demo Profile:
    - Monthly Salary: Rs. 120,000.00
    - Other Income: Rs. 10,000.00 (Freelance)
    - Total Monthly Income: Rs. 130,000.00
    - Monthly Essential Expenses: Rs. 45,000.00
    - Monthly EMIs: Rs. 15,000.00 (Personal Loan)
    - Total Monthly Outflows: Rs. 60,000.00
    - Net Monthly Surplus: Rs. 70,000.00
    - Savings Rate %: 65.38% (including Rs. 15,000 monthly investment)
    - DTI %: 11.54%
    - Total Assets: Rs. 720,000.00 (Savings 2.70L + FD 2.10L + MF 2.40L)
    - Total Liabilities: Rs. 450,000.00
    - Net Worth: Rs. 270,000.00 (Assets - Liabilities = 7.20L - 4.50L = 2.70L)
    - Emergency Buffer: Rs. 270,000.00 (6.0 Months)
    - Health Score: 100 / 100 (EXCELLENT)
    """
    profile = {
        "monthly_salary": 120000.0,
        "other_monthly_income": 10000.0,
        "monthly_expenses": 45000.0,
        "monthly_emi": 15000.0,
        "bank_balance": 250000.0,
        "existing_investments": 450000.0,
        "emergency_fund_balance": 270000.0,
        "target_emergency_months": 6,
        "monthly_sip": 15000.0,
        "income_sources": [
            {"name": "Primary Salary", "category": "Salary", "amount": 120000.0},
            {"name": "Freelance", "category": "Business", "amount": 10000.0}
        ],
        "expense_items": [
            {"name": "Rent", "category": "Essential", "amount": 22000.0},
            {"name": "Groceries", "category": "Essential", "amount": 12000.0},
            {"name": "Utilities", "category": "Essential", "amount": 5000.0},
            {"name": "Dining", "category": "Discretionary", "amount": 6000.0}
        ],
        "asset_items": [
            {"name": "Savings Account", "category": "Liquid", "amount": 270000.0},
            {"name": "Mutual Funds", "category": "Equity", "amount": 239955.70},
            {"name": "Fixed Deposits", "category": "Fixed Income", "amount": 210044.30}
        ],
        "liability_items": [
            {"name": "Personal Loan", "category": "Personal Loan", "principal_outstanding": 450000.0, "monthly_emi": 15000.0}
        ]
    }

    res = calculate_financial_health(profile)
    assert res["monthly_income"] == 130000.0
    assert res["monthly_expenses"] == 45000.0
    assert res["monthly_emis"] == 15000.0
    assert res["total_monthly_outflow"] == 60000.0
    assert res["monthly_surplus"] == 70000.0
    assert res["savings_rate_pct"] == 65.38
    assert res["debt_to_income_pct"] == 11.54
    assert res["total_assets"] == 720000.0
    assert res["total_liabilities"] == 450000.0
    assert res["net_worth"] == 270000.0
    assert res["emergency_coverage_months"] == 6.0
    assert res["health_score"] == 100
    assert res["health_status"] == "EXCELLENT"


def test_salary_plus_15_percent_reconciliation():
    baseline = {
        "monthly_salary": 120000.0,
        "other_monthly_income": 10000.0,
        "monthly_expenses": 45000.0,
        "monthly_emi": 15000.0,
        "income_sources": [
            {"name": "Primary Salary", "category": "Salary", "amount": 120000.0},
            {"name": "Freelance", "category": "Business", "amount": 10000.0}
        ]
    }

    res = simulate_what_if_scenario(
        baseline_profile=baseline,
        scenario_type="SALARY_CHANGE",
        scenario_params={"change_percentage": 15.0}
    )

    assert res["scenario_health"]["monthly_income"] == 148000.0
    assert res["baseline_health"]["monthly_surplus"] == 70000.0
    assert res["scenario_health"]["monthly_surplus"] == 88000.0
    assert res["deltas"]["surplus_change"] == 18000.0


def test_car_purchase_affordability_exact_reconciliation():
    res = calculate_purchase_affordability(
        purchase_price=1500000.0,
        down_payment=300000.0,
        loan_interest_rate_pct=8.5,
        loan_tenure_years=5.0,
        monthly_income=130000.0,
        monthly_expenses=45000.0,
        existing_emis=15000.0,
        emergency_fund_balance=270000.0,
        monthly_sip=15000.0,
        draw_down_payment_from_emergency=False
    )

    assert res["purchase_price"] == 1500000.0
    assert res["down_payment"] == 300000.0
    assert res["loan_amount"] == 1200000.0
    assert res["new_monthly_emi"] == 24619.84
    assert res["post_purchase_monthly_surplus"] == 45380.16
    assert res["new_debt_to_income_pct"] == 30.48
    assert res["affordability_assessment"] == "HIGHLY_AFFORDABLE"


def test_emi_engine_exact_reconciliation_and_schedule():
    res = calculate_emi_and_amortization(
        principal=1200000.0,
        annual_interest_rate_pct=8.5,
        tenure_months=60,
        generate_schedule=True
    )

    assert res["monthly_emi"] == 24619.84
    schedule = res["amortization_schedule"]
    assert len(schedule) == 60
    assert schedule[-1]["closing_balance"] == 0.00

    sum_principal = round(sum(s["principal_component"] for s in schedule), 2)
    assert abs(sum_principal - 1200000.0) <= 0.05


def test_goal_required_sip_canonical_reconciliation():
    g1 = calculate_goal_required_sip(
        target_amount=2500000.0,
        current_amount=450000.0,
        target_year=2030,
        expected_return_pct=10.0,
        current_year=2026
    )
    assert g1["target_amount"] == 2500000.0
    assert g1["current_amount"] == 450000.0
    assert g1["investment_horizon_years"] == 4
    assert g1["required_monthly_contribution"] > 0.0
    assert g1["status"] == "REQUIRES_CONTRIBUTION"


# --- NEW AUDIT REGRESSION TESTS ---

def test_affordability_valid_case():
    res = calculate_purchase_affordability(
        purchase_price=1500000.0,
        down_payment=300000.0,
        loan_interest_rate_pct=8.5,
        loan_tenure_years=5.0,
        monthly_income=130000.0,
        monthly_expenses=45000.0
    )
    assert res["loan_amount"] == 1200000.0
    assert res["new_monthly_emi"] == 24619.84


def test_affordability_boundary_down_payment_equals_price():
    res = calculate_purchase_affordability(
        purchase_price=500000.0,
        down_payment=500000.0,
        loan_interest_rate_pct=8.5,
        loan_tenure_years=5.0,
        monthly_income=130000.0,
        monthly_expenses=45000.0
    )
    assert res["loan_amount"] == 0.0
    assert res["new_monthly_emi"] == 0.0
    assert res["total_loan_interest"] == 0.0


def test_affordability_invalid_excessive_down_payment():
    with pytest.raises(ValueError, match="Down payment cannot exceed purchase price"):
        calculate_purchase_affordability(
            purchase_price=500000.0,
            down_payment=600000.0,
            loan_interest_rate_pct=8.5,
            loan_tenure_years=5.0,
            monthly_income=130000.0,
            monthly_expenses=45000.0
        )


def test_affordability_invalid_zero_car_price():
    with pytest.raises(ValueError, match="Car purchase price must be greater than 0"):
        calculate_purchase_affordability(
            purchase_price=0.0,
            down_payment=0.0,
            loan_interest_rate_pct=8.5,
            loan_tenure_years=5.0,
            monthly_income=130000.0,
            monthly_expenses=45000.0
        )


def test_scenario_salary_change_pass():
    p = {"monthly_salary": 120000.0, "monthly_expenses": 45000.0}
    res = simulate_what_if_scenario(p, "SALARY_CHANGE", {"change_percentage": 15.0})
    assert res["scenario_health"]["monthly_income"] == 138000.0


def test_scenario_expense_increase_pass():
    p = {"monthly_salary": 120000.0, "monthly_expenses": 45000.0}
    res = simulate_what_if_scenario(p, "EXPENSE_INCREASE", {"increase_percentage": 10.0})
    assert res["scenario_health"]["monthly_expenses"] == 49500.0


def test_scenario_increase_sip_pass():
    p = {"monthly_salary": 120000.0, "monthly_expenses": 45000.0, "monthly_sip": 10000.0}
    res = simulate_what_if_scenario(p, "INCREASE_SIP", {"additional_monthly_sip": 5000.0})
    assert "increased by ₹5,000.00" in res["impact_summary"]


def test_scenario_income_loss_pass():
    p = {"monthly_salary": 120000.0, "monthly_expenses": 45000.0, "bank_balance": 300000.0, "emergency_fund_balance": 300000.0}
    res = simulate_what_if_scenario(p, "INCOME_LOSS", {"duration_months": 3})
    assert res["scenario_health"]["monthly_income"] == 0.0


def test_scenario_unknown_type_error():
    p = {"monthly_salary": 120000.0, "monthly_expenses": 45000.0}
    with pytest.raises(ValueError, match="Unsupported scenario_type 'UNKNOWN_TYPE'"):
        simulate_what_if_scenario(p, "UNKNOWN_TYPE", {})
