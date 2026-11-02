from copy import deepcopy
from decimal import Decimal
from typing import Dict, Any, List
from app.engines.personal_finance import calculate_financial_health
from app.engines.affordability import calculate_purchase_affordability


def simulate_what_if_scenario(
    baseline_profile: Dict[str, Any],
    scenario_type: str,  # BUY_CAR, INCREASE_SIP, TAKE_LOAN, SALARY_CHANGE, EXPENSE_INCREASE, INCOME_LOSS, EMI_CHANGE, EXPENSE_CHANGE, SIP_CHANGE
    scenario_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Non-destructive What-If Scenario Simulator.
    Operates on an isolated in-memory copy of baseline_profile.
    Returns side-by-side comparison of baseline vs scenario metrics.
    NEVER mutates the real user's baseline financial profile in the database.
    """
    scenario_type_upper = scenario_type.upper()
    valid_scenarios = [
        "SALARY_CHANGE", "EXPENSE_INCREASE", "EXPENSE_CHANGE", "BUY_CAR",
        "INCREASE_SIP", "SIP_CHANGE", "INCOME_LOSS", "TAKE_LOAN", "EMI_CHANGE"
    ]
    if scenario_type_upper not in valid_scenarios:
        raise ValueError(f"Unsupported scenario_type '{scenario_type}'. Supported types: {', '.join(valid_scenarios)}.")

    # 1. Compute baseline financial health
    baseline_health = calculate_financial_health(baseline_profile)

    # 2. Create isolated copy for scenario transformation
    scenario_profile = deepcopy(baseline_profile)
    impact_summary = ""

    if scenario_type_upper == "SALARY_CHANGE":
        current_sal = float(baseline_profile.get("monthly_salary", 120000.0))
        if "additional_monthly_salary" in scenario_params:
            add_sal = float(scenario_params["additional_monthly_salary"])
            new_sal = max(0.0, current_sal + add_sal)
            delta_pct_float = ((new_sal - current_sal) / current_sal * 100.0) if current_sal > 0 else 0.0
            impact_summary = f"Simulated ₹{add_sal:+,.2f}/mo salary change: Monthly salary changes from ₹{current_sal:,.2f} to ₹{new_sal:,.2f}."
        elif "additional_annual_salary" in scenario_params:
            add_annual = float(scenario_params["additional_annual_salary"])
            add_sal = add_annual / 12.0
            new_sal = max(0.0, current_sal + add_sal)
            delta_pct_float = ((new_sal - current_sal) / current_sal * 100.0) if current_sal > 0 else 0.0
            impact_summary = f"Simulated ₹{add_annual:+,.2f}/yr salary change: Monthly salary changes from ₹{current_sal:,.2f} to ₹{new_sal:,.2f}."
        else:
            delta_pct_float = float(scenario_params.get("change_percentage", 15.0))
            new_sal = current_sal * (1.0 + (delta_pct_float / 100.0))
            impact_summary = f"Simulated {delta_pct_float:+.1f}% salary change: Monthly salary changes from ₹{current_sal:,.2f} to ₹{new_sal:,.2f}."

        scenario_profile["monthly_salary"] = new_sal

        # Update salary in income_sources if itemized list exists
        if "income_sources" in scenario_profile and scenario_profile["income_sources"]:
            updated_incomes = []
            multiplier = Decimal(str(new_sal)) / Decimal(str(current_sal)) if current_sal > 0 else Decimal("1")
            for inc in scenario_profile["income_sources"]:
                inc_copy = dict(inc)
                if inc_copy.get("category") == "Salary" or "salary" in inc_copy.get("name", "").lower():
                    amt_dec = Decimal(str(inc_copy["amount"]))
                    inc_copy["amount"] = amt_dec * multiplier
                updated_incomes.append(inc_copy)
            scenario_profile["income_sources"] = updated_incomes

    elif scenario_type_upper in ["EXPENSE_INCREASE", "EXPENSE_CHANGE"]:
        current_exp = float(baseline_profile.get("monthly_expenses", 45000.0))
        if "additional_monthly_expenses" in scenario_params:
            add_exp = float(scenario_params["additional_monthly_expenses"])
            new_exp = max(0.0, current_exp + add_exp)
            delta_pct_float = ((new_exp - current_exp) / current_exp * 100.0) if current_exp > 0 else 0.0
            impact_summary = f"Simulated ₹{add_exp:+,.2f}/mo expense change: Monthly living expenses change from ₹{current_exp:,.2f} to ₹{new_exp:,.2f}."
        else:
            delta_pct_float = float(scenario_params.get("increase_percentage", scenario_params.get("change_percentage", 15.0)))
            new_exp = current_exp * (1.0 + (delta_pct_float / 100.0))
            impact_summary = f"Simulated {delta_pct_float:+.1f}% expense change: Monthly living expenses change from ₹{current_exp:,.2f} to ₹{new_exp:,.2f}."

        scenario_profile["monthly_expenses"] = new_exp

        # Update expenses in expense_items if itemized list exists
        if "expense_items" in scenario_profile and scenario_profile["expense_items"]:
            updated_expenses = []
            multiplier = Decimal(str(new_exp)) / Decimal(str(current_exp)) if current_exp > 0 else Decimal("1")
            for exp in scenario_profile["expense_items"]:
                exp_copy = dict(exp)
                if exp_copy.get("category") != "EMI":
                    amt_dec = Decimal(str(exp_copy["amount"]))
                    exp_copy["amount"] = amt_dec * multiplier
                updated_expenses.append(exp_copy)
            scenario_profile["expense_items"] = updated_expenses

    elif scenario_type_upper == "BUY_CAR":
        car_price = float(scenario_params.get("car_price", 1500000.0))
        down_payment = float(scenario_params.get("down_payment", 300000.0))
        interest_rate = float(scenario_params.get("interest_rate_pct", 8.5))
        tenure_years = float(scenario_params.get("tenure_years", 5.0))

        affordability_res = calculate_purchase_affordability(
            purchase_price=car_price,
            down_payment=down_payment,
            loan_interest_rate_pct=interest_rate,
            loan_tenure_years=tenure_years,
            monthly_income=baseline_health["monthly_income"],
            monthly_expenses=baseline_health["monthly_expenses"],
            existing_emis=baseline_health["monthly_emis"],
            emergency_fund_balance=baseline_health["emergency_fund_balance"],
            monthly_sip=float(baseline_profile.get("monthly_sip", 0.0))
        )

        new_emi = affordability_res["new_monthly_emi"]
        scenario_profile["monthly_emi"] = baseline_health["monthly_emis"] + new_emi
        scenario_profile["bank_balance"] = max(0.0, float(baseline_profile.get("bank_balance", 0.0)) - down_payment)
        scenario_profile["emergency_fund_balance"] = affordability_res["emergency_fund_balance_after_down_payment"]

        # Add car EMI liability to liability_items
        liabilities = list(scenario_profile.get("liability_items", []))
        liabilities.append({
            "name": "New Car Loan",
            "category": "Car Loan",
            "principal_outstanding": affordability_res["loan_amount"],
            "monthly_emi": new_emi,
            "interest_rate_pct": interest_rate,
            "tenure_months_left": int(tenure_years * 12)
        })
        scenario_profile["liability_items"] = liabilities

        impact_summary = (
            f"Buying a ₹{car_price:,.0f} car with ₹{down_payment:,.0f} down payment adds a monthly EMI of ₹{new_emi:,.2f}. "
            f"Monthly surplus changes from ₹{baseline_health['monthly_surplus']:,.2f} to ₹{affordability_res['post_purchase_monthly_surplus']:,.2f}."
        )

    elif scenario_type_upper in ["INCREASE_SIP", "SIP_CHANGE"]:
        extra_sip = float(scenario_params.get("additional_monthly_sip", 5000.0))
        current_sip = float(baseline_profile.get("monthly_sip", 0.0))
        scenario_profile["monthly_sip"] = current_sip + extra_sip
        impact_summary = f"Monthly SIP investment increased by ₹{extra_sip:,.2f} to ₹{current_sip + extra_sip:,.2f} per month."

    elif scenario_type_upper == "INCOME_LOSS":
        months_loss = int(scenario_params.get("duration_months", 3))
        monthly_cost = baseline_health["monthly_expenses"] + baseline_health["monthly_emis"]
        total_drain = monthly_cost * months_loss

        scenario_profile["bank_balance"] = max(0.0, float(baseline_profile.get("bank_balance", 0.0)) - total_drain)
        scenario_profile["emergency_fund_balance"] = max(0.0, float(baseline_profile.get("emergency_fund_balance", 0.0)) - total_drain)
        scenario_profile["monthly_salary"] = 0.0
        scenario_profile["other_monthly_income"] = 0.0
        scenario_profile["income_sources"] = []

        impact_summary = f"Simulating {months_loss} months of zero income drains ₹{total_drain:,.2f} from liquid emergency funds."

    elif scenario_type_upper in ["TAKE_LOAN", "EMI_CHANGE"]:
        loan_amount = float(scenario_params.get("loan_amount", 0.0))
        loan_emi = float(scenario_params.get("monthly_emi", scenario_params.get("additional_monthly_emi", 10000.0)))

        scenario_profile["monthly_emi"] = baseline_health["monthly_emis"] + loan_emi
        liabilities = list(scenario_profile.get("liability_items", []))
        liabilities.append({
            "name": "New Loan",
            "category": "Loan",
            "principal_outstanding": loan_amount,
            "monthly_emi": loan_emi
        })
        scenario_profile["liability_items"] = liabilities
        impact_summary = f"Taking an additional monthly EMI of ₹{loan_emi:,.2f} changes total monthly debt obligations to ₹{scenario_profile['monthly_emi']:,.2f}."

    # 3. Compute scenario financial health
    scenario_health = calculate_financial_health(scenario_profile)

    return {
        "scenario_type": scenario_type,
        "scenario_params": scenario_params,
        "impact_summary": impact_summary,
        "baseline_health": baseline_health,
        "scenario_health": scenario_health,
        "deltas": {
            "surplus_change": round(scenario_health["monthly_surplus"] - baseline_health["monthly_surplus"], 2),
            "savings_rate_change_pct": round(scenario_health["savings_rate_pct"] - baseline_health["savings_rate_pct"], 2),
            "dti_change_pct": round(scenario_health["debt_to_income_pct"] - baseline_health["debt_to_income_pct"], 2),
            "emergency_coverage_change_months": round(scenario_health["emergency_coverage_months"] - baseline_health["emergency_coverage_months"], 2),
            "health_score_change": scenario_health["health_score"] - baseline_health["health_score"]
        }
    }
