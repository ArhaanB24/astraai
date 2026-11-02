import pytest
from decimal import Decimal
from app.services.intent_classifier import (
    intent_classifier,
    Domain,
    MutualFundIntent,
    MutualFundSubIntent,
    PersonalFinanceIntent,
    TaxIntent,
    IntentResult
)
from app.services.scenario_extractor import scenario_extractor, apply_salary_scenario, ScenarioType, ChangeType
from app.engines.tax import compare_tax_regimes, FinancialYear
from app.engines.affordability import calculate_purchase_affordability
from app.engines.personal_finance import calculate_financial_health, calculate_goal_required_sip
from app.engines.scenario_simulator import simulate_what_if_scenario


# =============================================================================
# 1. MUTUAL FUND SEMANTIC INTENT UNDERSTANDING (12+ TESTS)
# =============================================================================

@pytest.mark.parametrize("query,expected_intent", [
    ("How is my portfolio doing?", MutualFundIntent.PORTFOLIO_SUMMARY.value),
    ("How are my investments performing?", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("Am I making money?", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("What is my current portfolio value?", MutualFundIntent.PORTFOLIO_SUMMARY.value),
    ("How much have I invested?", MutualFundIntent.PORTFOLIO_SUMMARY.value),
    ("Tell me about my investments", MutualFundIntent.PORTFOLIO_SUMMARY.value),
    ("What is my return?", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("Why are my returns low?", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("Why is my portfolio underperforming?", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("How much profit have I made?", MutualFundIntent.PORTFOLIO_SUMMARY.value),
    ("What is my XIRR?", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("Explain my XIRR", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("What is my annualized return?", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("Explain CAGR", MutualFundIntent.PORTFOLIO_PERFORMANCE.value),
    ("Which fund is performing best?", MutualFundIntent.BEST_PERFORMING_FUND.value),
    ("Which fund is performing worst?", MutualFundIntent.WORST_PERFORMING_FUND.value),
    ("Which one is dragging my portfolio down?", MutualFundIntent.WORST_PERFORMING_FUND.value),
    ("Tell me about my HDFC fund", MutualFundIntent.FUND_DETAILS.value),
    ("Do my funds overlap?", MutualFundIntent.FUND_OVERLAP.value),
    ("Am I overexposed to banking?", MutualFundIntent.FUND_OVERLAP.value),
    ("How risky is my portfolio?", MutualFundIntent.RISK_ANALYSIS.value),
    ("What is my Sharpe ratio?", MutualFundIntent.RISK_ANALYSIS.value),
    ("What is my maximum drawdown?", MutualFundIntent.RISK_ANALYSIS.value),
    ("What mutual funds can I invest in?", MutualFundIntent.FUND_DISCOVERY.value),
    ("Which mutual funds are available?", MutualFundIntent.FUND_DISCOVERY.value),
    ("Show my transactions", MutualFundIntent.TRANSACTION_HISTORY.value),
    ("Show my SIPs", MutualFundIntent.TRANSACTION_HISTORY.value),
    ("What happens if I invest another ₹10,000 every month?", MutualFundIntent.SIP_SCENARIO.value),
    ("What changed in my portfolio?", MutualFundIntent.PORTFOLIO_CHANGES.value),
    ("What is NAV?", MutualFundIntent.GENERAL_FINANCE_QUESTION.value),
    ("What is an index fund?", MutualFundIntent.GENERAL_FINANCE_QUESTION.value),
    ("Tata power stock news today", MutualFundIntent.LIVE_MARKET_NEWS.value)
])
def test_mutual_fund_semantic_intents(query, expected_intent):
    res: IntentResult = intent_classifier.classify(query, Domain.MUTUAL_FUND)
    assert res.intent == expected_intent
    assert res.domain == Domain.MUTUAL_FUND


# =============================================================================
# 2. PERSONAL FINANCE SEMANTIC INTENT UNDERSTANDING (10+ TESTS)
# =============================================================================

@pytest.mark.parametrize("query,expected_intent", [
    ("How healthy are my finances?", PersonalFinanceIntent.FINANCIAL_HEALTH_BUDGET.value),
    ("Am I spending too much?", PersonalFinanceIntent.FINANCIAL_HEALTH_BUDGET.value),
    ("How much do I have left every month?", PersonalFinanceIntent.FINANCIAL_HEALTH_BUDGET.value),
    ("What is my monthly surplus?", PersonalFinanceIntent.FINANCIAL_HEALTH_BUDGET.value),
    ("Can I afford a ₹10 lakh car?", PersonalFinanceIntent.AFFORDABILITY_CHECK.value),
    ("Would a 10 lakh car be affordable for me?", PersonalFinanceIntent.AFFORDABILITY_CHECK.value),
    ("What if I buy a 15L car?", PersonalFinanceIntent.AFFORDABILITY_CHECK.value),
    ("What if my salary rises by 1 lakh?", PersonalFinanceIntent.WHAT_IF_SCENARIO.value),
    ("What if my expenses increase by 20%?", PersonalFinanceIntent.WHAT_IF_SCENARIO.value),
    ("What happens if my EMI increases by ₹10,000?", PersonalFinanceIntent.WHAT_IF_SCENARIO.value),
    ("How much SIP do I need for my house?", PersonalFinanceIntent.GOAL_PLANNING.value),
    ("How much emergency fund should I keep?", PersonalFinanceIntent.EMERGENCY_FUND.value),
    ("What is DTI?", PersonalFinanceIntent.GENERAL_EDUCATION.value),
    ("Explain the 50/30/20 rule", PersonalFinanceIntent.GENERAL_EDUCATION.value)
])
def test_personal_finance_semantic_intents(query, expected_intent):
    res: IntentResult = intent_classifier.classify(query, Domain.PERSONAL_FINANCE)
    assert res.intent == expected_intent
    assert res.domain == Domain.PERSONAL_FINANCE


# =============================================================================
# 3. TAX SEMANTIC INTENT UNDERSTANDING (10+ TESTS)
# =============================================================================

@pytest.mark.parametrize("query,expected_intent", [
    ("How much tax will I pay?", TaxIntent.REGIME_COMPARISON.value),
    ("Which regime is better?", TaxIntent.REGIME_COMPARISON.value),
    ("Which tax regime saves me money?", TaxIntent.REGIME_COMPARISON.value),
    ("Compare my tax regimes", TaxIntent.REGIME_COMPARISON.value),
    ("What if my salary increases by ₹1 lakh?", TaxIntent.TAX_SCENARIO.value),
    ("What if I get a 5 lakh raise?", TaxIntent.TAX_SCENARIO.value),
    ("What happens to my tax if I earn 20% more?", TaxIntent.TAX_SCENARIO.value),
    ("How much additional tax will I pay after a 1L raise?", TaxIntent.TAX_SCENARIO.value),
    ("How does Section 80C save tax?", TaxIntent.DEDUCTION_OPTIMIZATION.value),
    ("How much can I claim under 80D?", TaxIntent.DEDUCTION_OPTIMIZATION.value),
    ("Does ELSS reduce my tax?", TaxIntent.DEDUCTION_OPTIMIZATION.value),
    ("Explain 87A", TaxIntent.REBATE_MARGINAL_RELIEF.value),
    ("Why am I not getting the 87A rebate?", TaxIntent.REBATE_MARGINAL_RELIEF.value),
    ("What is Section 115BAC?", TaxIntent.STATUTORY_EDUCATION.value),
    ("What is the difference between FY and AY?", TaxIntent.STATUTORY_EDUCATION.value)
])
def test_tax_semantic_intents(query, expected_intent):
    res: IntentResult = intent_classifier.classify(query, Domain.TAX)
    assert res.intent == expected_intent
    assert res.domain == Domain.TAX


# =============================================================================
# 4. FOLLOW-UP CONTEXT & PRONOUN RESOLUTION (4 TESTS)
# =============================================================================

def test_follow_up_xirr_is_that_good():
    history = [
        {"role": "user", "content": "What is my XIRR?"},
        {"role": "assistant", "content": "Your portfolio XIRR is 51.00% calculated deterministically."}
    ]
    res = intent_classifier.classify("Is that good?", Domain.MUTUAL_FUND, history)
    assert res.is_follow_up is True
    assert res.intent == MutualFundIntent.XIRR_CAGR_PERFORMANCE.value
    assert res.follow_up_target == "XIRR_BENCHMARK_INTERPRETATION"


def test_follow_up_worst_fund_why():
    history = [
        {"role": "user", "content": "Which fund is performing worst?"},
        {"role": "assistant", "content": "Your lowest performing fund is Axis Bluechip Fund with underperformance."}
    ]
    res = intent_classifier.classify("Why?", Domain.MUTUAL_FUND, history)
    assert res.is_follow_up is True
    assert res.intent in [MutualFundIntent.WORST_PERFORMING_FUND.value, MutualFundIntent.FUND_DETAILS.value]
    assert res.follow_up_target == "LAGGING_FUND_DIAGNOSIS"


def test_follow_up_car_affordability_what_about_10l():
    history = [
        {"role": "user", "content": "Can I afford a 15 lakh car?"},
        {"role": "assistant", "content": "Evaluating ₹15 Lakh car with ₹3 Lakh down payment."}
    ]
    res = intent_classifier.classify("What about 10 lakh?", Domain.PERSONAL_FINANCE, history)
    assert res.is_follow_up is True
    assert res.intent == PersonalFinanceIntent.AFFORDABILITY_CHECK.value
    assert res.parameters.get("purchase_price") == 1000000.0


def test_follow_up_tax_salary_raise():
    history = [
        {"role": "user", "content": "What tax will I pay?"},
        {"role": "assistant", "content": "Your total tax liability under New Regime is ₹1,06,860."}
    ]
    res = intent_classifier.classify("What if my salary rises by 2L?", Domain.TAX, history)
    assert res.is_follow_up is True
    assert res.intent == TaxIntent.TAX_SCENARIO.value
    assert res.parameters.get("salary_delta") == 200000.0


# =============================================================================
# 5. OUT-OF-DOMAIN DETECTION (3 TESTS)
# =============================================================================

def test_out_of_domain_tax_in_mutual_fund():
    res = intent_classifier.classify("How much income tax do I pay under old vs new regime?", Domain.MUTUAL_FUND)
    assert res.is_out_of_domain is True
    assert res.suggested_domain == Domain.TAX


def test_out_of_domain_tax_query_in_mutual_fund_exact():
    res = intent_classifier.classify("How much income tax do I owe?", Domain.MUTUAL_FUND)
    assert res.is_out_of_domain is True
    assert res.suggested_domain == Domain.TAX


def test_out_of_domain_mutual_fund_in_tax():
    res = intent_classifier.classify("Which mutual fund has highest stock overlap?", Domain.TAX)
    assert res.is_out_of_domain is True
    assert res.suggested_domain == Domain.MUTUAL_FUND


def test_out_of_domain_mutual_fund_query_in_tax_exact():
    res = intent_classifier.classify("Which mutual fund in my portfolio is performing worst?", Domain.TAX)
    assert res.is_out_of_domain is True
    assert res.suggested_domain == Domain.MUTUAL_FUND


def test_out_of_domain_portfolio_in_personal_finance():
    res = intent_classifier.classify("What is my portfolio XIRR and Sharpe ratio?", Domain.PERSONAL_FINANCE)
    assert res.is_out_of_domain is True
    assert res.suggested_domain == Domain.MUTUAL_FUND


def test_out_of_domain_tax_regime_in_personal_finance_exact():
    res = intent_classifier.classify("Which tax regime should I choose?", Domain.PERSONAL_FINANCE)
    assert res.is_out_of_domain is True
    assert res.suggested_domain == Domain.TAX


def test_non_ood_false_positives():
    res1 = intent_classifier.classify("How financially healthy am I?", Domain.PERSONAL_FINANCE)
    assert res1.is_out_of_domain is False

    res2 = intent_classifier.classify("What happens if my salary increases by 20%?", Domain.PERSONAL_FINANCE)
    assert res2.is_out_of_domain is False


def test_tax_scenario_context_preservation():
    history = [
        {"role": "user", "content": "What if my salary increases by 5 lakhs?"},
        {"role": "assistant", "content": "If your salary increases by ₹5,00,000 to ₹19,40,000, your tax delta under new regime is +₹98,020."}
    ]
    res = intent_classifier.classify("How much extra tax is that?", Domain.TAX, conversation_history=history)
    assert res.intent == TaxIntent.TAX_SCENARIO.value
    assert float(res.parameters.get("change_amount", 0.0)) == 500000.0
    assert res.is_follow_up is True


def test_personal_finance_affordability_context_preservation():
    history = [
        {"role": "user", "content": "Can I afford a ₹15 lakh car?"},
        {"role": "assistant", "content": "Car purchase affordability assessment for ₹15 Lakh car with ₹3 Lakh down payment."}
    ]

    # Turn 2: Down payment update
    res2 = intent_classifier.classify("What if I put 5 lakhs down?", Domain.PERSONAL_FINANCE, conversation_history=history)
    assert res2.intent == PersonalFinanceIntent.AFFORDABILITY_CHECK.value
    assert float(res2.parameters.get("purchase_price")) == 1500000.0
    assert float(res2.parameters.get("down_payment")) == 500000.0

    # Turn 3: EMI question
    history.append({"role": "user", "content": "What if I put 5 lakhs down?"})
    history.append({"role": "assistant", "content": "Updated down payment to ₹5,00,000. Loan principal: ₹10,00,000."})
    res3 = intent_classifier.classify("How much EMI would I have?", Domain.PERSONAL_FINANCE, conversation_history=history)
    assert res3.intent == PersonalFinanceIntent.AFFORDABILITY_CHECK.value
    assert float(res3.parameters.get("purchase_price")) == 1500000.0
    assert float(res3.parameters.get("down_payment")) == 500000.0

    # Turn 4: Safety question
    history.append({"role": "user", "content": "How much EMI would I have?"})
    history.append({"role": "assistant", "content": "Estimated monthly EMI is ₹20,516.53."})
    res4 = intent_classifier.classify("Would that be safe for me?", Domain.PERSONAL_FINANCE, conversation_history=history)
    assert res4.intent == PersonalFinanceIntent.AFFORDABILITY_CHECK.value
    assert float(res4.parameters.get("purchase_price")) == 1500000.0
    assert float(res4.parameters.get("down_payment")) == 500000.0


def test_mutual_fund_comparison_best_fund_context():
    history = [
        {"role": "user", "content": "Which fund is doing the worst?"},
        {"role": "assistant", "content": "Lowest performing fund is Parag Parikh Flexi Cap Fund."}
    ]
    res = intent_classifier.classify("compare it with the best one", Domain.MUTUAL_FUND, conversation_history=history)
    assert res.intent == MutualFundIntent.FUND_LEVEL_ANALYSIS.value
    assert res.sub_intent == MutualFundSubIntent.FUND_COMPARISON.value
    assert res.entities.get("primary_fund") == "Parag Parikh Flexi Cap Fund - Direct Plan - Growth"
    assert res.entities.get("secondary_fund") == "best"


def test_unrelated_context_reset():
    history = [
        {"role": "user", "content": "What if my salary increases by 5 lakhs?"},
        {"role": "assistant", "content": "Scenario salary becomes ₹19,40,000."}
    ]
    res = intent_classifier.classify("Which mutual fund is doing the worst?", Domain.MUTUAL_FUND, conversation_history=history)
    assert res.intent == MutualFundIntent.WORST_PERFORMING_FUND.value
    assert res.is_out_of_domain is False

    res3 = intent_classifier.classify("Can I afford a 15 lakh car?", Domain.PERSONAL_FINANCE)
    assert res3.is_out_of_domain is False

    res4 = intent_classifier.classify("Which fund is doing the worst?", Domain.MUTUAL_FUND)
    assert res4.is_out_of_domain is False

    res5 = intent_classifier.classify("What is my XIRR?", Domain.MUTUAL_FUND)
    assert res5.is_out_of_domain is False


# =============================================================================
# 6. MISSING PARAMETERS & CONVERSATIONAL (3 TESTS)
# =============================================================================

def test_missing_parameters_car_affordability_without_price():
    res = intent_classifier.classify("Can I afford to buy a car?", Domain.PERSONAL_FINANCE)
    assert "purchase_price" in res.missing_parameters
    assert res.clarification_prompt is not None


def test_missing_parameters_sip_scenario_without_amount():
    res = intent_classifier.classify("What happens if I invest monthly in SIP?", Domain.MUTUAL_FUND)
    assert "additional_monthly_amount" in res.missing_parameters
    assert res.clarification_prompt is not None


def test_conversational_greeting_across_domains():
    for domain in [Domain.MUTUAL_FUND, Domain.PERSONAL_FINANCE, Domain.TAX]:
        res = intent_classifier.classify("Hello! What can you do?", domain)
        assert res.intent == "conversational"


# =============================================================================
# 7. ZERO-LLM-ARITHMETIC & DYNAMIC PARAMETER PRESERVATION (4 TESTS)
# =============================================================================

def test_tax_scenario_dynamic_deltas_differ_by_amount():
    """Verify that +₹1L, +₹5L, and +20% produce strictly different deterministic numbers."""
    base_sal = Decimal("1440000.0")
    
    # 1 Lakh Raise
    ext_1l = scenario_extractor.extract_scenario("What if my salary increases by 1 lakh?")
    sal_1l, delta_1l, _ = apply_salary_scenario(base_sal, ext_1l)
    assert sal_1l == Decimal("1540000.0")
    tax_1l = compare_tax_regimes(gross_salary=float(sal_1l), financial_year=FinancialYear.FY_2025_26)

    # 5 Lakh Raise
    ext_5l = scenario_extractor.extract_scenario("What if my salary increases by 5 lakh?")
    sal_5l, delta_5l, _ = apply_salary_scenario(base_sal, ext_5l)
    assert sal_5l == Decimal("1940000.0")
    tax_5l = compare_tax_regimes(gross_salary=float(sal_5l), financial_year=FinancialYear.FY_2025_26)

    # 20% Raise
    ext_20pct = scenario_extractor.extract_scenario("What if my salary increases by 20%?")
    sal_20pct, delta_20pct, _ = apply_salary_scenario(base_sal, ext_20pct)
    assert sal_20pct == Decimal("1728000.0")
    tax_20pct = compare_tax_regimes(gross_salary=float(sal_20pct), financial_year=FinancialYear.FY_2025_26)

    # Validate distinct deterministic tax liabilities
    assert tax_1l["new_regime"]["total_tax_liability"] < tax_20pct["new_regime"]["total_tax_liability"] < tax_5l["new_regime"]["total_tax_liability"]


def test_car_affordability_dynamic_prices_differ():
    """Verify that ₹10L vs ₹15L car produces distinct deterministic EMIs and DTI ratios."""
    res_10l = calculate_purchase_affordability(
        purchase_price=1000000.0,
        down_payment=200000.0,
        loan_interest_rate_pct=8.5,
        loan_tenure_years=5.0,
        monthly_income=120000.0,
        monthly_expenses=50000.0,
        existing_emis=15000.0,
        emergency_fund_balance=270000.0
    )

    res_15l = calculate_purchase_affordability(
        purchase_price=1500000.0,
        down_payment=300000.0,
        loan_interest_rate_pct=8.5,
        loan_tenure_years=5.0,
        monthly_income=120000.0,
        monthly_expenses=50000.0,
        existing_emis=15000.0,
        emergency_fund_balance=270000.0
    )

    assert res_10l["loan_amount"] == 800000.0
    assert res_15l["loan_amount"] == 1200000.0
    assert res_10l["new_monthly_emi"] < res_15l["new_monthly_emi"]
    assert res_10l["post_purchase_monthly_surplus"] > res_15l["post_purchase_monthly_surplus"]


def test_vehicle_affordability_parameters_and_types():
    res_scooter = intent_classifier.classify("Can I afford a ₹10,000 scooter?", Domain.PERSONAL_FINANCE)
    assert res_scooter.parameters.get("purchase_price") == 10000.0
    assert res_scooter.parameters.get("vehicle_type") == "scooter"
    assert res_scooter.parameters.get("down_payment_supplied") is False

    res_bike = intent_classifier.classify("Can I afford a 1 lakh bike?", Domain.PERSONAL_FINANCE)
    assert res_bike.parameters.get("purchase_price") == 100000.0
    assert res_bike.parameters.get("vehicle_type") == "bike"

    res_car = intent_classifier.classify("Can I afford a ₹15 lakh car?", Domain.PERSONAL_FINANCE)
    assert res_car.parameters.get("purchase_price") == 1500000.0
    assert res_car.parameters.get("vehicle_type") == "car"

    res_moto = intent_classifier.classify("What if I buy a ₹2 lakh motorcycle?", Domain.PERSONAL_FINANCE)
    assert res_moto.parameters.get("purchase_price") == 200000.0
    assert res_moto.parameters.get("vehicle_type") == "motorcycle"

    res_dp = intent_classifier.classify("Can I afford a ₹1 lakh bike with ₹20,000 down payment?", Domain.PERSONAL_FINANCE)
    assert res_dp.parameters.get("purchase_price") == 100000.0
    assert res_dp.parameters.get("down_payment") == 20000.0
    assert res_dp.parameters.get("down_payment_supplied") is True

    res_no_price = intent_classifier.classify("What happens to my finances if I buy a scooter?", Domain.PERSONAL_FINANCE)
    assert "purchase_price" in res_no_price.missing_parameters


def test_mutual_fund_sub_intents_and_follow_up_entities():
    # 1. WHY + fund entity
    res1 = intent_classifier.classify("Why is my Parag Parikh fund performing badly?", Domain.MUTUAL_FUND)
    assert res1.intent == MutualFundIntent.FUND_LEVEL_ANALYSIS.value
    assert res1.sub_intent == "fund_why_underperforming"
    assert "Parag Parikh" in res1.entities.get("primary_fund", "")

    # 2. SELL/HOLD + fund entity
    res2 = intent_classifier.classify("Should I sell Parag Parikh Flexi Cap Fund?", Domain.MUTUAL_FUND)
    assert res2.sub_intent == "fund_sell_hold_decision"

    # 3. Pronoun "it" follow-up after worst fund identification
    history = [
        {"role": "user", "content": "Which fund is performing the worst?"},
        {"role": "assistant", "content": "Lowest Performing Fund: Parag Parikh Flexi Cap Fund - Direct Plan - Growth"}
    ]
    res3 = intent_classifier.classify("Why?", Domain.MUTUAL_FUND, history)
    assert res3.sub_intent == "fund_why_underperforming"
    assert "Parag Parikh" in res3.entities.get("primary_fund", "")

    # 4. Pronoun "this fund" follow-up for sell/hold
    res4 = intent_classifier.classify("Should I sell this fund?", Domain.MUTUAL_FUND, history)
    assert res4.sub_intent == "fund_sell_hold_decision"
    assert "Parag Parikh" in res4.entities.get("primary_fund", "")

    # 5. Pronoun "that fund" follow-up for risk
    res5 = intent_classifier.classify("Is that fund risky?", Domain.MUTUAL_FUND, history)
    assert res5.sub_intent == "fund_risk_analysis"
    assert "Parag Parikh" in res5.entities.get("primary_fund", "")

    # 6. Fund comparison with Axis
    res6 = intent_classifier.classify("Compare it with my Axis fund.", Domain.MUTUAL_FUND, history)
    assert res6.sub_intent == "fund_comparison"
    assert "Parag Parikh" in res6.entities.get("primary_fund", "")
    assert "Axis" in res6.entities.get("secondary_fund", "")

    # 7. Return follow-up
    res7 = intent_classifier.classify("What is its return?", Domain.MUTUAL_FUND, history)
    assert res7.sub_intent == "fund_performance"
    assert "Parag Parikh" in res7.entities.get("primary_fund", "")


def test_least_performing_ranking_and_data_integrity():
    # 1. "which fund is least performing" resolves to WORST_PERFORMING_FUND
    res = intent_classifier.classify("which fund is least performing", Domain.MUTUAL_FUND)
    assert res.intent == MutualFundIntent.WORST_PERFORMING_FUND.value

    # 2. Test portfolio metrics data integrity check
    summary = {
        "total_invested": 490000.0,
        "current_value": 484390.21,
        "total_profit_loss": -5609.79,
        "fund_breakdown": [
            {
                "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
                "invested_amount": 120000.0,
                "current_value": 118609.79,
                "profit_loss": -1390.21,
                "allocation_pct": 24.5
            },
            {
                "scheme_name": "Axis ELSS- Tax Saver Fund - Direct Plan - Growth Option",
                "invested_amount": 100000.0,
                "current_value": 108450.00,
                "profit_loss": 8450.0,
                "allocation_pct": 22.4
            }
        ]
    }
    
    fund_breakdown = summary["fund_breakdown"]
    sorted_by_pl = sorted(fund_breakdown, key=lambda x: x.get("profit_loss", 0.0))
    worst_fund = sorted_by_pl[0]
    
    assert worst_fund["scheme_name"] == "Parag Parikh Flexi Cap Fund - Direct Plan - Growth"
    assert worst_fund["invested_amount"] == 120000.0
    assert worst_fund["current_value"] == 118609.79
    assert worst_fund["profit_loss"] == -1390.21
    assert worst_fund["allocation_pct"] == 24.5

    # 3. Follow-up "why?" preserves primary_fund
    history = [
        {"role": "user", "content": "which fund is least performing"},
        {"role": "assistant", "content": "Lowest Performing Fund: Parag Parikh Flexi Cap Fund - Direct Plan - Growth"}
    ]
    res_why = intent_classifier.classify("why?", Domain.MUTUAL_FUND, history)
    assert res_why.sub_intent == "fund_why_underperforming"
    assert "Parag Parikh" in res_why.entities.get("primary_fund", "")

    # 4. Follow-up "should I sell it?" preserves primary_fund
    res_sell = intent_classifier.classify("should I sell it?", Domain.MUTUAL_FUND, history)
    assert res_sell.sub_intent == "fund_sell_hold_decision"
    assert "Parag Parikh" in res_sell.entities.get("primary_fund", "")

    # 5. Follow-up "is it risky?" preserves primary_fund
    res_risk = intent_classifier.classify("is it risky?", Domain.MUTUAL_FUND, history)
    assert res_risk.sub_intent == "fund_risk_analysis"
    assert "Parag Parikh" in res_risk.entities.get("primary_fund", "")

    # 6. Follow-up "what is its return?" preserves primary_fund
    res_ret = intent_classifier.classify("what is its return?", Domain.MUTUAL_FUND, history)
    assert res_ret.sub_intent == "fund_performance"
    assert "Parag Parikh" in res_ret.entities.get("primary_fund", "")


def test_underperformance_semantic_variations_and_general_education():
    history = [
        {"role": "user", "content": "which fund is least performing"},
        {"role": "assistant", "content": "Lowest Performing Fund: Parag Parikh Flexi Cap Fund - Direct Plan - Growth"}
    ]

    semantic_why_queries = [
        "why is this fund underperforming?",
        "why is it doing badly?",
        "what is causing this fund's poor performance?",
        "why did this fund perform worse?",
        "why is Parag Parikh doing badly?",
        "what is dragging this fund down?",
        "why is this my worst fund?",
        "why?",
        "what is causing that?",
        "is it because of its holdings?"
    ]

    for q in semantic_why_queries:
        res = intent_classifier.classify(q, Domain.MUTUAL_FUND, history)
        assert res.intent in [MutualFundIntent.WORST_PERFORMING_FUND.value, MutualFundIntent.FUND_DETAILS.value], f"Failed for query: {q}"
        assert res.sub_intent == "fund_why_underperforming", f"Failed sub_intent for query: {q}"
        assert "Parag Parikh" in res.entities.get("primary_fund", ""), f"Failed entity preservation for query: {q}"

    # General education vs portfolio analysis queries
    edu_res1 = intent_classifier.classify("What does expense ratio mean?", Domain.MUTUAL_FUND)
    assert edu_res1.intent in [MutualFundIntent.GENERAL_FINANCE_QUESTION.value, MutualFundIntent.GENERAL_EDUCATION.value]

    edu_res2 = intent_classifier.classify("What is an equity mutual fund?", Domain.MUTUAL_FUND)
    assert edu_res2.intent in [MutualFundIntent.GENERAL_FINANCE_QUESTION.value, MutualFundIntent.GENERAL_EDUCATION.value]

    edu_res3 = intent_classifier.classify("How does a flexi cap fund work?", Domain.MUTUAL_FUND)
    assert edu_res3.intent in [MutualFundIntent.GENERAL_FINANCE_QUESTION.value, MutualFundIntent.GENERAL_EDUCATION.value]

    port_res1 = intent_classifier.classify("Why is my fund's expense ratio hurting returns?", Domain.MUTUAL_FUND, history)
    assert port_res1.intent in [MutualFundIntent.WORST_PERFORMING_FUND.value, MutualFundIntent.FUND_DETAILS.value]
    assert port_res1.sub_intent == "fund_why_underperforming"




