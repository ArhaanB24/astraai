from decimal import Decimal
import pytest
from app.engines.tax import (
    calculate_income_tax,
    compare_tax_regimes,
    TaxRegime,
    FinancialYear,
    round_nearest_10
)
from app.agents.tax_agent import tax_agent


def test_zero_income():
    """TC-1: Zero income produces zero tax across both regimes."""
    res_new = calculate_income_tax(gross_salary=0, other_income=0, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_new["taxable_income"] == 0.0
    assert res_new["total_tax_liability"] == 0.0

    res_old = calculate_income_tax(gross_salary=0, other_income=0, regime=TaxRegime.OLD, financial_year=FinancialYear.FY_2025_26)
    assert res_old["taxable_income"] == 0.0
    assert res_old["total_tax_liability"] == 0.0


def test_basic_exemption_and_rebate_fy25_new():
    """T25-02 & T25-06: FY 2025-26 New Regime basic exemption and full 87A rebate."""
    # Exactly ₹4,00,000 taxable income -> 0% slab
    res_4l = calculate_income_tax(gross_salary=475000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_4l["taxable_income"] == 400000.0
    assert res_4l["total_tax_liability"] == 0.0

    # Exactly ₹12,00,000 taxable income -> Slab tax ₹60,000 completely absorbed by 87A rebate
    res_12l = calculate_income_tax(gross_salary=1275000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_12l["taxable_income"] == 1200000.0
    assert res_12l["tax_before_rebate"] == 60000.0
    assert res_12l["section_87a_rebate"] == 60000.0
    assert res_12l["total_tax_liability"] == 0.0


def test_marginal_relief_fy25_new_regime():
    """T25-07 & boundary checks: Marginal relief under Section 87A for New Regime."""
    # ₹12,00,001 taxable income -> Excess is ₹1 -> Tax before cess is ₹1 -> Final rounded tax = ₹0
    res_1 = calculate_income_tax(gross_salary=1275001, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_1["taxable_income"] == 1200000.0  # Sec 288A rounded down to 12L
    assert res_1["total_tax_liability"] == 0.0

    # ₹12,05,000 taxable income -> Excess ₹5,000 -> Tax before cess = ₹5,000 + 4% cess (₹200) = ₹5,200
    res_5k = calculate_income_tax(gross_salary=1280000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_5k["taxable_income"] == 1205000.0
    assert res_5k["marginal_relief"] == 55750.0
    assert res_5k["tax_after_rebate"] == 5000.0
    assert res_5k["health_and_education_cess"] == 200.0
    assert res_5k["total_tax_liability"] == 5200.0

    # ₹12,10,000 taxable income -> Excess ₹10,000 -> Tax before cess = ₹10,000 + 4% cess (₹400) = ₹10,400
    res_10k = calculate_income_tax(gross_salary=1285000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_10k["taxable_income"] == 1210000.0
    assert res_10k["marginal_relief"] == 51500.0
    assert res_10k["tax_after_rebate"] == 10000.0
    assert res_10k["health_and_education_cess"] == 400.0
    assert res_10k["total_tax_liability"] == 10400.0


def test_fy25_higher_slabs_new_regime():
    """T25-08 to T25-11: Slabs beyond 12L in FY 2025-26 New Regime."""
    # ₹16,00,000 taxable income (Gross ₹16.75L)
    res_16l = calculate_income_tax(gross_salary=1675000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_16l["taxable_income"] == 1600000.0
    assert res_16l["tax_before_rebate"] == 120000.0
    assert res_16l["health_and_education_cess"] == 4800.0
    assert res_16l["total_tax_liability"] == 124800.0

    # ₹20,00,000 taxable income (Gross ₹20.75L)
    res_20l = calculate_income_tax(gross_salary=2075000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_20l["taxable_income"] == 2000000.0
    assert res_20l["tax_before_rebate"] == 200000.0
    assert res_20l["health_and_education_cess"] == 8000.0
    assert res_20l["total_tax_liability"] == 208000.0

    # ₹24,00,000 taxable income (Gross ₹24.75L) - Corrected Cess Verification
    res_24l = calculate_income_tax(gross_salary=2475000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_24l["taxable_income"] == 2400000.0
    assert res_24l["tax_before_rebate"] == 300000.0
    assert res_24l["health_and_education_cess"] == 12000.0
    assert res_24l["total_tax_liability"] == 312000.0

    # ₹30,00,000 taxable income (Gross ₹30.75L)
    res_30l = calculate_income_tax(gross_salary=3075000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2025_26)
    assert res_30l["taxable_income"] == 3000000.0
    assert res_30l["tax_before_rebate"] == 480000.0
    assert res_30l["health_and_education_cess"] == 19200.0
    assert res_30l["total_tax_liability"] == 499200.0


def test_fy24_new_regime_rules():
    """Verify FY 2024-25 New Regime slabs (₹7L rebate threshold)."""
    # ₹7,75,000 Gross -> ₹75k std ded -> ₹7,00,000 Taxable -> Full ₹25k rebate -> ₹0 tax
    res_775k = calculate_income_tax(gross_salary=775000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2024_25)
    assert res_775k["taxable_income"] == 700000.0
    assert res_775k["tax_before_rebate"] == 20000.0
    assert res_775k["section_87a_rebate"] == 20000.0
    assert res_775k["total_tax_liability"] == 0.0

    # ₹7,80,000 Gross -> ₹7,05,000 Taxable -> Marginal relief: Tax pre-cess = ₹5,000 -> Total = ₹5,200
    res_780k = calculate_income_tax(gross_salary=780000, is_salaried=True, regime=TaxRegime.NEW, financial_year=FinancialYear.FY_2024_25)
    assert res_780k["taxable_income"] == 705000.0
    assert res_780k["tax_after_rebate"] == 5000.0
    assert res_780k["total_tax_liability"] == 5200.0


def test_old_regime_80c_and_80d_capping():
    """80C capped at ₹1,50,000 and 80D capped appropriately."""
    # User claims ₹2,50,000 in 80C -> Must be capped at ₹1,50,000
    res = calculate_income_tax(
        gross_salary=1200000,
        deductions_80c=250000,
        deductions_80d=35000,
        regime=TaxRegime.OLD,
        financial_year=FinancialYear.FY_2025_26
    )
    assert res["eligible_80c_deduction"] == 150000.0
    assert res["eligible_80d_deduction"] == 35000.0
    assert res["standard_deduction"] == 50000.0
    assert res["total_deductions"] == 235000.0
    assert res["taxable_income"] == 965000.0


def test_chapter_6a_disallowed_in_new_regime():
    """80C and 80D are strictly disallowed in New Regime."""
    res = calculate_income_tax(
        gross_salary=1500000,
        deductions_80c=150000,
        deductions_80d=25000,
        regime=TaxRegime.NEW,
        financial_year=FinancialYear.FY_2025_26
    )
    assert res["eligible_80c_deduction"] == 0.0
    assert res["eligible_80d_deduction"] == 0.0
    assert res["standard_deduction"] == 75000.0
    assert res["total_deductions"] == 75000.0
    assert res["taxable_income"] == 1425000.0


def test_senior_citizen_old_regime():
    """Senior Citizen (Age 65) gets ₹3,00,000 basic exemption in Old Regime."""
    res = calculate_income_tax(
        gross_salary=600000,
        deductions_80c=50000,
        regime=TaxRegime.OLD,
        financial_year=FinancialYear.FY_2025_26,
        age=65
    )
    # Gross ₹6L - Std Ded ₹50k - 80C ₹50k = Taxable ₹5,00,000
    assert res["taxable_income"] == 500000.0
    # Slabs: 0-3L Nil, 3L-5L @ 5% = ₹10,000. Sec 87A rebate = ₹10,000 -> Tax = ₹0
    assert res["tax_before_rebate"] == 10000.0
    assert res["section_87a_rebate"] == 10000.0
    assert res["total_tax_liability"] == 0.0


def test_canonical_demo_user_alex_sharma():
    """TC-COMP-2: Canonical user Alex Sharma (Gross ₹15.6L = ₹14.4L Sal + ₹1.2L Other)."""
    comp = compare_tax_regimes(
        gross_salary=1440000,
        other_income=120000,
        deductions_80c=150000,
        deductions_80d=25000,
        financial_year=FinancialYear.FY_2025_26,
        is_salaried=True,
        age=28
    )
    # Old Regime: Taxable ₹13,35,000 -> Tax = ₹2,21,520
    assert comp["old_regime"]["taxable_income"] == 1335000.0
    assert comp["old_regime"]["total_tax_liability"] == 221520.0

    # New Regime: Taxable ₹14,85,000 -> Tax = ₹1,06,860
    assert comp["new_regime"]["taxable_income"] == 1485000.0
    assert comp["new_regime"]["total_tax_liability"] == 106860.0

    # Recommendation
    assert comp["recommended_regime"] == "NEW"
    assert comp["tax_savings"] == 114660.0


def test_negative_validations():
    """Input boundary validation: Negative salary, income, or deductions must raise ValueError."""
    with pytest.raises(ValueError, match="Gross salary cannot be negative"):
        calculate_income_tax(gross_salary=-50000)

    with pytest.raises(ValueError, match="Other income cannot be negative"):
        calculate_income_tax(gross_salary=500000, other_income=-10000)

    with pytest.raises(ValueError, match="Tax deductions cannot be negative"):
        calculate_income_tax(gross_salary=500000, deductions_80c=-20000)

    with pytest.raises(ValueError, match="Invalid age"):
        calculate_income_tax(gross_salary=500000, age=-5)

    with pytest.raises(ValueError, match="Unsupported financial year"):
        calculate_income_tax(gross_salary=500000, financial_year="1999-00")


def test_statutory_rounding_sections_288a_and_288b():
    """Section 288A (Taxable Income to nearest ₹10) and Section 288B (Tax to nearest ₹10)."""
    assert round_nearest_10(Decimal("1234.4")) == Decimal("1230")
    assert round_nearest_10(Decimal("1235.0")) == Decimal("1240")
    assert round_nearest_10(Decimal("1238.9")) == Decimal("1240")


def test_tax_agent_deterministic_routing():
    """Verify TaxAgent tools and deterministic context assembly."""
    profile = {
        "monthly_salary": 120000.0,
        "other_monthly_income": 10000.0,
        "age": 28,
        "employment_type": "Salaried",
        "existing_investments": 450000.0,
        "elss_investments_annual": 150000.0
    }
    
    # Run agent query without DB mock (None db)
    res = tax_agent.process_query(
        db=None,
        user_id="test-user-id",
        profile_dict=profile,
        query="Which tax regime is better for me?"
    )
    
    assert res is not None
    assert "deterministic_tax_summary" in res
    assert "compare_tax_regimes" in res["tools_used"]
    assert res["deterministic_tax_summary"]["recommended_regime"] == "NEW"
    assert "answer" in res
    assert len(res["answer"]) > 0
