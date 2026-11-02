from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Any
from enum import Enum


class TaxRegime(str, Enum):
    OLD = "OLD"
    NEW = "NEW"


class FinancialYear(str, Enum):
    FY_2024_25 = "2024-25"
    FY_2025_26 = "2025-26"


@dataclass(frozen=True)
class TaxSlab:
    lower: Decimal
    upper: Optional[Decimal]
    rate: Decimal


@dataclass(frozen=True)
class TaxRuleSet:
    financial_year: FinancialYear
    assessment_year: str
    regime: TaxRegime
    standard_deduction: Decimal
    slabs: List[TaxSlab]
    sec_87a_income_limit: Decimal
    sec_87a_max_rebate: Decimal
    has_87a_marginal_relief: bool
    allows_chapter_6a: bool
    sec_80c_cap: Decimal
    sec_80d_self_cap: Decimal
    sec_80d_parents_cap: Decimal
    cess_rate: Decimal = Decimal("0.04")


# Statutory Immutable Rule Registry for Supported Financial Years
TAX_RULE_REGISTRY: Dict[Tuple[FinancialYear, TaxRegime], TaxRuleSet] = {
    # FY 2025-26 (AY 2026-27) - New Tax Regime (Current Statutory Framework)
    (FinancialYear.FY_2025_26, TaxRegime.NEW): TaxRuleSet(
        financial_year=FinancialYear.FY_2025_26,
        assessment_year="2026-27",
        regime=TaxRegime.NEW,
        standard_deduction=Decimal("75000"),
        slabs=[
            TaxSlab(Decimal("0"), Decimal("400000"), Decimal("0.00")),
            TaxSlab(Decimal("400000"), Decimal("800000"), Decimal("0.05")),
            TaxSlab(Decimal("800000"), Decimal("1200000"), Decimal("0.10")),
            TaxSlab(Decimal("1200000"), Decimal("1600000"), Decimal("0.15")),
            TaxSlab(Decimal("1600000"), Decimal("2000000"), Decimal("0.20")),
            TaxSlab(Decimal("2000000"), Decimal("2400000"), Decimal("0.25")),
            TaxSlab(Decimal("2400000"), None, Decimal("0.30")),
        ],
        sec_87a_income_limit=Decimal("1200000"),
        sec_87a_max_rebate=Decimal("60000"),
        has_87a_marginal_relief=True,
        allows_chapter_6a=False,
        sec_80c_cap=Decimal("0"),
        sec_80d_self_cap=Decimal("0"),
        sec_80d_parents_cap=Decimal("0"),
        cess_rate=Decimal("0.04"),
    ),
    # FY 2025-26 (AY 2026-27) - Old Tax Regime
    (FinancialYear.FY_2025_26, TaxRegime.OLD): TaxRuleSet(
        financial_year=FinancialYear.FY_2025_26,
        assessment_year="2026-27",
        regime=TaxRegime.OLD,
        standard_deduction=Decimal("50000"),
        slabs=[
            TaxSlab(Decimal("0"), Decimal("250000"), Decimal("0.00")),
            TaxSlab(Decimal("250000"), Decimal("500000"), Decimal("0.05")),
            TaxSlab(Decimal("500000"), Decimal("1000000"), Decimal("0.20")),
            TaxSlab(Decimal("1000000"), None, Decimal("0.30")),
        ],
        sec_87a_income_limit=Decimal("500000"),
        sec_87a_max_rebate=Decimal("12500"),
        has_87a_marginal_relief=False,
        allows_chapter_6a=True,
        sec_80c_cap=Decimal("150000"),
        sec_80d_self_cap=Decimal("25000"),
        sec_80d_parents_cap=Decimal("50000"),
        cess_rate=Decimal("0.04"),
    ),
    # FY 2024-25 (AY 2025-26) - New Tax Regime (Budget 2024 Baseline)
    (FinancialYear.FY_2024_25, TaxRegime.NEW): TaxRuleSet(
        financial_year=FinancialYear.FY_2024_25,
        assessment_year="2025-26",
        regime=TaxRegime.NEW,
        standard_deduction=Decimal("75000"),
        slabs=[
            TaxSlab(Decimal("0"), Decimal("300000"), Decimal("0.00")),
            TaxSlab(Decimal("300000"), Decimal("700000"), Decimal("0.05")),
            TaxSlab(Decimal("700000"), Decimal("1000000"), Decimal("0.10")),
            TaxSlab(Decimal("1000000"), Decimal("1200000"), Decimal("0.15")),
            TaxSlab(Decimal("1200000"), Decimal("1500000"), Decimal("0.20")),
            TaxSlab(Decimal("1500000"), None, Decimal("0.30")),
        ],
        sec_87a_income_limit=Decimal("700000"),
        sec_87a_max_rebate=Decimal("25000"),
        has_87a_marginal_relief=True,
        allows_chapter_6a=False,
        sec_80c_cap=Decimal("0"),
        sec_80d_self_cap=Decimal("0"),
        sec_80d_parents_cap=Decimal("0"),
        cess_rate=Decimal("0.04"),
    ),
    # FY 2024-25 (AY 2025-26) - Old Tax Regime
    (FinancialYear.FY_2024_25, TaxRegime.OLD): TaxRuleSet(
        financial_year=FinancialYear.FY_2024_25,
        assessment_year="2025-26",
        regime=TaxRegime.OLD,
        standard_deduction=Decimal("50000"),
        slabs=[
            TaxSlab(Decimal("0"), Decimal("250000"), Decimal("0.00")),
            TaxSlab(Decimal("250000"), Decimal("500000"), Decimal("0.05")),
            TaxSlab(Decimal("500000"), Decimal("1000000"), Decimal("0.20")),
            TaxSlab(Decimal("1000000"), None, Decimal("0.30")),
        ],
        sec_87a_income_limit=Decimal("500000"),
        sec_87a_max_rebate=Decimal("12500"),
        has_87a_marginal_relief=False,
        allows_chapter_6a=True,
        sec_80c_cap=Decimal("150000"),
        sec_80d_self_cap=Decimal("25000"),
        sec_80d_parents_cap=Decimal("50000"),
        cess_rate=Decimal("0.04"),
    ),
}


def round_nearest_10(amount: Decimal) -> Decimal:
    """
    Statutory rounding off to the nearest multiple of Rs. 10 under Section 288A & 288B.
    If the last digit is 5 or more, round up; otherwise round down.
    """
    return (amount / Decimal("10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("10")


def to_decimal(val: Any) -> Decimal:
    """Helper to safely convert numeric or string inputs into exact Decimal."""
    if val is None:
        return Decimal("0")
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def parse_financial_year(fy_str: str) -> FinancialYear:
    """Parses and validates supported financial year strings."""
    clean = fy_str.strip().replace("FY", "").replace(" ", "").replace("_", "-")
    if clean in ["2025-26", "2025-2026", "25-26"]:
        return FinancialYear.FY_2025_26
    elif clean in ["2024-25", "2024-2025", "24-25"]:
        return FinancialYear.FY_2024_25
    raise ValueError(f"Unsupported financial year: '{fy_str}'. Supported years are '2024-25' and '2025-26'.")


def parse_tax_regime(regime_str: str) -> TaxRegime:
    """Parses and validates tax regime strings."""
    clean = regime_str.strip().upper()
    if clean in ["NEW", "NEW_REGIME", "NEW REGIME", "115BAC"]:
        return TaxRegime.NEW
    elif clean in ["OLD", "OLD_REGIME", "OLD REGIME", "REGULAR"]:
        return TaxRegime.OLD
    raise ValueError(f"Unsupported tax regime: '{regime_str}'. Supported regimes are 'OLD' and 'NEW'.")


def calculate_income_tax(
    gross_salary: Any = Decimal("0"),
    other_income: Any = Decimal("0"),
    deductions_80c: Any = Decimal("0"),
    deductions_80d: Any = Decimal("0"),
    other_deductions: Any = Decimal("0"),
    regime: Any = TaxRegime.NEW,
    financial_year: Any = FinancialYear.FY_2025_26,
    is_salaried: bool = True,
    age: int = 28
) -> Dict[str, Any]:
    """
    Deterministic Income Tax Calculation Engine.
    Executes 100% exact Decimal calculations following the Income Tax Act, 1961.
    """
    d_salary = to_decimal(gross_salary)
    d_other = to_decimal(other_income)
    d_80c = to_decimal(deductions_80c)
    d_80d = to_decimal(deductions_80d)
    d_other_ded = to_decimal(other_deductions)

    # 1. Input Boundary Validations
    if d_salary < Decimal("0"):
        raise ValueError(f"Gross salary cannot be negative (received: ₹{d_salary:,.2f}).")
    if d_other < Decimal("0"):
        raise ValueError(f"Other income cannot be negative (received: ₹{d_other:,.2f}).")
    if d_80c < Decimal("0") or d_80d < Decimal("0") or d_other_ded < Decimal("0"):
        raise ValueError("Tax deductions cannot be negative.")
    if age < 0 or age > 120:
        raise ValueError(f"Invalid age: {age}. Age must be between 0 and 120.")

    # 2. Parse Financial Year & Regime
    if isinstance(financial_year, str):
        parsed_fy = parse_financial_year(financial_year)
    else:
        parsed_fy = financial_year

    if isinstance(regime, str):
        parsed_regime = parse_tax_regime(regime)
    else:
        parsed_regime = regime

    ruleset = TAX_RULE_REGISTRY.get((parsed_fy, parsed_regime))
    if not ruleset:
        raise ValueError(f"No tax rule set configured for {parsed_fy.value} ({parsed_regime.value} regime).")

    # 3. Income & Deductions Aggregation
    gross_total_income = d_salary + d_other

    # Standard Deduction (only against salary income for salaried individuals)
    if is_salaried and d_salary > Decimal("0"):
        standard_deduction = min(d_salary, ruleset.standard_deduction)
    else:
        standard_deduction = Decimal("0")

    # Chapter VI-A Deductions (Only if allowed by regime)
    if ruleset.allows_chapter_6a:
        eligible_80c = min(d_80c, ruleset.sec_80c_cap)
        # 80D max cap: non-senior parent (25k) vs senior parent (50k)
        max_80d = ruleset.sec_80d_self_cap + ruleset.sec_80d_parents_cap
        eligible_80d = min(d_80d, max_80d)
        eligible_other_ded = d_other_ded
    else:
        eligible_80c = Decimal("0")
        eligible_80d = Decimal("0")
        eligible_other_ded = Decimal("0")

    total_deductions = standard_deduction + eligible_80c + eligible_80d + eligible_other_ded

    # Raw Taxable Income
    raw_taxable_income = max(Decimal("0"), gross_total_income - total_deductions)

    # 4. Section 288A Rounding of Taxable Income
    taxable_income = round_nearest_10(raw_taxable_income)

    # 5. Progressive Slab Tax Calculation
    # Handle Old Regime Senior Citizen basic exemption adjustments
    if parsed_regime == TaxRegime.OLD:
        if age >= 80:
            basic_exemption = Decimal("500000")
        elif age >= 60:
            basic_exemption = Decimal("300000")
        else:
            basic_exemption = Decimal("250000")

        slab_breakdown = []
        slab_tax = Decimal("0")

        # Slab 1: Basic Exemption to 5L @ 5%
        if taxable_income > basic_exemption:
            taxable_in_slab1 = min(taxable_income - basic_exemption, Decimal("500000") - basic_exemption)
            tax_slab1 = taxable_in_slab1 * Decimal("0.05")
            slab_tax += tax_slab1
            slab_breakdown.append({"slab": f"₹{basic_exemption:,.0f} to ₹5,00,000", "rate": "5%", "tax": float(tax_slab1)})

        # Slab 2: 5L to 10L @ 20%
        if taxable_income > Decimal("500000"):
            taxable_in_slab2 = min(taxable_income - Decimal("500000"), Decimal("500000"))
            tax_slab2 = taxable_in_slab2 * Decimal("0.20")
            slab_tax += tax_slab2
            slab_breakdown.append({"slab": "₹5,00,001 to ₹10,00,000", "rate": "20%", "tax": float(tax_slab2)})

        # Slab 3: Above 10L @ 30%
        if taxable_income > Decimal("1000000"):
            taxable_in_slab3 = taxable_income - Decimal("1000000")
            tax_slab3 = taxable_in_slab3 * Decimal("0.30")
            slab_tax += tax_slab3
            slab_breakdown.append({"slab": "Above ₹10,00,000", "rate": "30%", "tax": float(tax_slab3)})
    else:
        # New Regime Slabs
        slab_breakdown = []
        slab_tax = Decimal("0")
        for slab in ruleset.slabs:
            if slab.rate == Decimal("0"):
                continue
            if taxable_income > slab.lower:
                if slab.upper is not None:
                    taxable_in_slab = min(taxable_income - slab.lower, slab.upper - slab.lower)
                    slab_desc = f"₹{slab.lower:,.0f} to ₹{slab.upper:,.0f}"
                else:
                    taxable_in_slab = taxable_income - slab.lower
                    slab_desc = f"Above ₹{slab.lower:,.0f}"
                
                tax_slab = taxable_in_slab * slab.rate
                slab_tax += tax_slab
                slab_breakdown.append({"slab": slab_desc, "rate": f"{int(slab.rate * 100)}%", "tax": float(tax_slab)})

    tax_before_rebate = slab_tax

    # 6. Section 87A Rebate & Marginal Relief
    rebate = Decimal("0")
    marginal_relief = Decimal("0")
    tax_after_rebate = slab_tax

    if taxable_income <= ruleset.sec_87a_income_limit:
        rebate = min(slab_tax, ruleset.sec_87a_max_rebate)
        tax_after_rebate = max(Decimal("0"), slab_tax - rebate)
    elif ruleset.has_87a_marginal_relief:
        excess_income = taxable_income - ruleset.sec_87a_income_limit
        if slab_tax > excess_income:
            marginal_relief = slab_tax - excess_income
            tax_after_rebate = excess_income

    # 7. Surcharge & Surcharge Marginal Relief (if income > 50L)
    surcharge = Decimal("0")
    if taxable_income > Decimal("50000000"):
        # Above 5 Cr: 37% in Old, capped at 25% in New
        s_rate = Decimal("0.25") if parsed_regime == TaxRegime.NEW else Decimal("0.37")
        surcharge = tax_after_rebate * s_rate
    elif taxable_income > Decimal("20000000"):
        surcharge = tax_after_rebate * Decimal("0.25")
    elif taxable_income > Decimal("10000000"):
        surcharge = tax_after_rebate * Decimal("0.15")
    elif taxable_income > Decimal("5000000"):
        surcharge = tax_after_rebate * Decimal("0.10")

    # 8. Health & Education Cess (4%)
    cess = (tax_after_rebate + surcharge) * ruleset.cess_rate

    # 9. Section 288B Final Rounding of Tax Liability
    total_tax_liability = round_nearest_10(tax_after_rebate + surcharge + cess)

    # Effective tax rate and monthly equivalent
    if gross_total_income > Decimal("0"):
        effective_rate = round(float((total_tax_liability / gross_total_income) * Decimal("100")), 2)
    else:
        effective_rate = 0.0

    monthly_tax = round(float(total_tax_liability / Decimal("12")), 2)

    return {
        "financial_year": parsed_fy.value,
        "assessment_year": ruleset.assessment_year,
        "tax_regime": parsed_regime.value,
        "gross_salary": float(d_salary),
        "other_income": float(d_other),
        "gross_total_income": float(gross_total_income),
        "standard_deduction": float(standard_deduction),
        "eligible_80c_deduction": float(eligible_80c),
        "eligible_80d_deduction": float(eligible_80d),
        "total_deductions": float(total_deductions),
        "taxable_income": float(taxable_income),
        "slab_breakdown": slab_breakdown,
        "tax_before_rebate": float(tax_before_rebate),
        "section_87a_rebate": float(rebate),
        "marginal_relief": float(marginal_relief),
        "tax_after_rebate": float(tax_after_rebate),
        "surcharge": float(surcharge),
        "health_and_education_cess": float(cess),
        "total_tax_liability": float(total_tax_liability),
        "effective_tax_rate_pct": effective_rate,
        "monthly_tax_equivalent": monthly_tax,
        "disclaimer": "Estimates based on applicable statutory Finance Act tax rules. Not professional legal or CA tax advice."
    }


def compare_tax_regimes(
    gross_salary: Any = Decimal("0"),
    other_income: Any = Decimal("0"),
    deductions_80c: Any = Decimal("0"),
    deductions_80d: Any = Decimal("0"),
    other_deductions: Any = Decimal("0"),
    financial_year: Any = FinancialYear.FY_2025_26,
    is_salaried: bool = True,
    age: int = 28
) -> Dict[str, Any]:
    """
    Compares Old Tax Regime vs New Tax Regime side-by-side.
    Provides authoritative deterministic recommendation and savings delta.
    """
    old_res = calculate_income_tax(
        gross_salary=gross_salary,
        other_income=other_income,
        deductions_80c=deductions_80c,
        deductions_80d=deductions_80d,
        other_deductions=other_deductions,
        regime=TaxRegime.OLD,
        financial_year=financial_year,
        is_salaried=is_salaried,
        age=age
    )

    new_res = calculate_income_tax(
        gross_salary=gross_salary,
        other_income=other_income,
        deductions_80c=deductions_80c,
        deductions_80d=deductions_80d,
        other_deductions=other_deductions,
        regime=TaxRegime.NEW,
        financial_year=financial_year,
        is_salaried=is_salaried,
        age=age
    )

    old_tax = Decimal(str(old_res["total_tax_liability"]))
    new_tax = Decimal(str(new_res["total_tax_liability"]))

    if new_tax < old_tax:
        recommended = "NEW"
        savings = float(old_tax - new_tax)
    elif old_tax < new_tax:
        recommended = "OLD"
        savings = float(new_tax - old_tax)
    else:
        recommended = "EITHER"
        savings = 0.0

    return {
        "financial_year": old_res["financial_year"],
        "assessment_year": old_res["assessment_year"],
        "gross_total_income": old_res["gross_total_income"],
        "old_regime": old_res,
        "new_regime": new_res,
        "recommended_regime": recommended,
        "tax_savings": savings,
        "summary": (
            f"The {recommended} Regime saves you ₹{savings:,.2f} annually in tax."
            if recommended != "EITHER"
            else "Both tax regimes yield the identical tax liability."
        )
    }
