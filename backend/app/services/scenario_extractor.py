import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ScenarioType(str, Enum):
    SALARY_CHANGE = "SALARY_CHANGE"
    EXPENSE_CHANGE = "EXPENSE_CHANGE"
    SIP_CHANGE = "SIP_CHANGE"
    EMI_CHANGE = "EMI_CHANGE"
    OTHER_INCOME_CHANGE = "OTHER_INCOME_CHANGE"
    CAR_AFFORDABILITY = "CAR_AFFORDABILITY"
    PORTFOLIO_SHOCK = "PORTFOLIO_SHOCK"
    GOAL_MODIFICATION = "GOAL_MODIFICATION"


class ChangeType(str, Enum):
    ABSOLUTE = "ABSOLUTE"
    PERCENTAGE = "PERCENTAGE"
    SET_VALUE = "SET_VALUE"


@dataclass
class AffordabilityExtractedParams:
    purchase_price: Optional[Decimal] = None
    down_payment: Optional[Decimal] = None
    interest_rate_pct: Optional[Decimal] = None
    loan_tenure_years: Optional[Decimal] = None
    loan_tenure_months: Optional[Decimal] = None


@dataclass
class ScenarioExtractionResult:
    is_conversational: bool = False
    is_scenario: bool = False
    scenario_type: Optional[ScenarioType] = None
    change_type: Optional[ChangeType] = None
    change_amount: Optional[Decimal] = None
    change_percentage: Optional[Decimal] = None
    target_value: Optional[Decimal] = None
    affordability_params: Optional[AffordabilityExtractedParams] = None
    raw_query: str = ""
    description: str = ""


class ScenarioExtractor:
    """
    Centralized Natural Language Scenario & Parameter Extraction Service.
    
    Transforms varied natural-language modifications into structured, deterministic parameters
    without performing final financial calculations.
    All mathematical operations (addition, multiplication, tax deltas) remain strictly in Python.
    """

    CONVERSATIONAL_WORDS = {
        "hi", "hello", "hey", "who are you", "what can you do", "help",
        "good morning", "good evening", "thanks", "thank you", "bye", "goodbye"
    }

    @staticmethod
    def parse_inr_amount(text: str) -> Optional[Decimal]:
        """
        Parses monetary expressions such as:
        - "₹1 lakh", "1.5 lakhs", "1L", "1 lac", "10 lakhs"
        - "₹1 crore", "2 crores", "1.5 cr"
        - "10k", "50 k", "₹5,000", "50,000"
        - "100000", "1440000"
        """
        if not text:
            return None

        clean = text.strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("rs.", "").replace("rs", "").strip()

        # Check for Crore (10,000,000)
        cr_match = re.search(r'([\d\.]+)\s*(?:crores?|cr|crs)\b', clean, re.IGNORECASE)
        if cr_match:
            return (Decimal(cr_match.group(1)) * Decimal("10000000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Check for Lakh (100,000)
        lakh_match = re.search(r'([\d\.]+)\s*(?:lakhs?|lacs?|lac|l)\b', clean, re.IGNORECASE)
        if lakh_match:
            return (Decimal(lakh_match.group(1)) * Decimal("100000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Check for Thousand / K (1,000)
        k_match = re.search(r'([\d\.]+)\s*(?:thousand|k)\b', clean, re.IGNORECASE)
        if k_match:
            return (Decimal(k_match.group(1)) * Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Plain number
        num_match = re.search(r'([\d\.]+)', clean)
        if num_match:
            return Decimal(num_match.group(1)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return None

    def extract_scenario(self, query: str) -> ScenarioExtractionResult:
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # 1. Conversational Intent Check
        stripped_punct = re.sub(r'[^\w\s]', '', q_lower).strip()
        if stripped_punct in self.CONVERSATIONAL_WORDS:
            return ScenarioExtractionResult(is_conversational=True, raw_query=query, description="Conversational greeting")

        # Direction checks
        is_increase = any(w in q_lower for w in ["increase", "increases", "increased", "goes up", "go up", "rose", "rise", "raise", "jump", "grow", "add", "additional", "more", "+", "hike"])
        is_decrease = any(w in q_lower for w in ["decrease", "decreases", "decreased", "drop", "drops", "dropped", "fall", "falls", "fell", "cut", "reduce", "reduces", "reduced", "loss", "less", "-"])
        multiplier = Decimal("-1") if is_decrease else Decimal("1")

        # 2. Car / Purchase Affordability Extraction
        if any(w in q_lower for w in ["car", "vehicle", "auto loan", "buy a car", "afford a car", "afford"]):
            aff_params = AffordabilityExtractedParams()
            is_affordability = False

            # Price extraction (e.g. "₹10 lakh car", "car costs ₹12 lakh", "buy a 15L car", "₹10 lakh")
            price_match = re.search(r'(?:cost(?:s)?|price|worth|buy|afford)?\s*(?:a|an)?\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|crores?|cr|k)?)\s*(?:car|vehicle|purchase)?', q_lower)
            if price_match:
                parsed_p = self.parse_inr_amount(price_match.group(1))
                if parsed_p and parsed_p >= Decimal("50000"):
                    aff_params.purchase_price = parsed_p
                    is_affordability = True

            # Down payment extraction:
            # Pattern A: "with ₹3 lakh down payment", "₹3 lakh down"
            dp_match_a = re.search(r'(?:with|put|pay)?\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|k)?)\s*(?:down\s*payment|down|upfront)', q_lower)
            # Pattern B: "down payment of ₹3 lakh"
            dp_match_b = re.search(r'(?:down\s*payment|down|upfront)\s*(?:of|is)?\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|k)?)', q_lower)

            if dp_match_a and self.parse_inr_amount(dp_match_a.group(1)):
                aff_params.down_payment = self.parse_inr_amount(dp_match_a.group(1))
                is_affordability = True
            elif dp_match_b and self.parse_inr_amount(dp_match_b.group(1)):
                aff_params.down_payment = self.parse_inr_amount(dp_match_b.group(1))
                is_affordability = True

            # Interest rate extraction (e.g. "at 9% interest", "interest rate is 8.5%", "rate is 9%")
            rate_match = re.search(r'(?:interest|rate|roi)?\s*(?:is|at|of)?\s*([\d\.]+)\s*%\s*(?:interest|rate)?', q_lower)
            if rate_match:
                aff_params.interest_rate_pct = Decimal(rate_match.group(1))
                is_affordability = True

            # Tenure extraction (e.g. "for 5 years", "choose 7 years", "60 months")
            yr_match = re.search(r'(\d+)\s*(?:years?|yrs?)\b', q_lower)
            if yr_match:
                aff_params.loan_tenure_years = Decimal(yr_match.group(1))
                aff_params.loan_tenure_months = Decimal(yr_match.group(1)) * Decimal("12")
                is_affordability = True
            else:
                mo_match = re.search(r'(\d+)\s*(?:months?|mos?)\b', q_lower)
                if mo_match:
                    aff_params.loan_tenure_months = Decimal(mo_match.group(1))
                    aff_params.loan_tenure_years = Decimal(mo_match.group(1)) / Decimal("12")
                    is_affordability = True

            if is_affordability:
                return ScenarioExtractionResult(
                    is_scenario=True,
                    scenario_type=ScenarioType.CAR_AFFORDABILITY,
                    affordability_params=aff_params,
                    raw_query=query,
                    description=f"Car affordability check with price: {aff_params.purchase_price}, down payment: {aff_params.down_payment}"
                )

        # 3. SIP / Investment Scenario (Check first to avoid colliding with generic words)
        if any(w in q_lower for w in ["sip", "invest", "investment", "monthly investment"]):
            delta_match = re.search(r'(?:increase|add|invest|more|by)?\s*(?:another|additional)?\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|k)?)\s*(?:sip|monthly|every month)?', q_lower)
            if delta_match:
                amount = self.parse_inr_amount(delta_match.group(1))
                if amount and amount >= Decimal("500"):
                    amount_val = amount * multiplier
                    return ScenarioExtractionResult(
                        is_scenario=True,
                        scenario_type=ScenarioType.SIP_CHANGE,
                        change_type=ChangeType.ABSOLUTE,
                        change_amount=amount_val,
                        raw_query=query,
                        description=f"SIP modification of {amount_val:+,} INR"
                    )

        # 4. Additional EMI Scenario
        if any(w in q_lower for w in ["emi", "loan emi", "new emi", "debt"]):
            delta_match = re.search(r'(?:additional|new|take|pay|of)?\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|k)?)\s*(?:emi)?', q_lower)
            if delta_match:
                amount = self.parse_inr_amount(delta_match.group(1))
                if amount and amount >= Decimal("100"):
                    return ScenarioExtractionResult(
                        is_scenario=True,
                        scenario_type=ScenarioType.EMI_CHANGE,
                        change_type=ChangeType.ABSOLUTE,
                        change_amount=amount,
                        raw_query=query,
                        description=f"Additional recurring EMI of ₹{amount:,}"
                    )

        # 5. Expense Scenario
        if any(w in q_lower for w in ["expense", "expenses", "spending", "cost of living", "inflation"]):
            pct_match = re.search(r'([\d\.]+)\s*%', q_lower)
            if pct_match:
                pct_val = Decimal(pct_match.group(1)) * multiplier
                return ScenarioExtractionResult(
                    is_scenario=True,
                    scenario_type=ScenarioType.EXPENSE_CHANGE,
                    change_type=ChangeType.PERCENTAGE,
                    change_percentage=pct_val,
                    raw_query=query,
                    description=f"Expense percentage change of {pct_val}%"
                )

            delta_match = re.search(r'(?:by|of)?\s*(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|k)?)\b', q_lower)
            if delta_match:
                amount = self.parse_inr_amount(delta_match.group(1))
                if amount:
                    amount_val = amount * multiplier
                    return ScenarioExtractionResult(
                        is_scenario=True,
                        scenario_type=ScenarioType.EXPENSE_CHANGE,
                        change_type=ChangeType.ABSOLUTE,
                        change_amount=amount_val,
                        raw_query=query,
                        description=f"Expense absolute delta of {amount_val:+,} INR"
                    )

        # 6. Salary / Income Scenario
        if any(w in q_lower for w in [
            "salary", "income", "raise", "earnings", "hike", "paycheck", "earn", "earns", "earning",
            "make", "makes", "making", "take home", "ctc", "package", "lpa", "per month", "per year",
            "monthly", "annually", "a month", "a year", "a annum", "per annum"
        ]):
            is_monthly = any(w in q_lower for w in ["per month", "a month", "monthly", "/month", "/mo", "pm", "p.m."])

            # Case A: Percentage change (e.g. "salary increases by 10%", "20% raise", "salary drops by 15%")
            pct_match = re.search(r'(?:by|of)?\s*([\d\.]+)\s*%\s*(?:raise|hike|increase|decrease|drop|cut|more|less)?', q_lower)
            if pct_match and ("%" in q_lower or "percent" in q_lower):
                pct_val = Decimal(pct_match.group(1)) * multiplier
                return ScenarioExtractionResult(
                    is_scenario=True,
                    scenario_type=ScenarioType.SALARY_CHANGE,
                    change_type=ChangeType.PERCENTAGE,
                    change_percentage=pct_val,
                    raw_query=query,
                    description=f"Salary percentage change of {pct_val}%"
                )

            # Case B: Absolute delta (e.g. "salary increases by ₹1 lakh", "increase salary by 100000", "salary decreases by ₹50,000", "earn 2 lakhs more")
            delta_match = re.search(r'(?:increase|increases|increased|decrease|decreases|decreased|drop|drops|dropped|fall|falls|raise|add|cut|by|more|less)\s+(?:by\s+)?(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|crores?|cr|k)?)\b', q_lower)
            if not delta_match:
                delta_match = re.search(r'(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|crores?|cr|k)?)\s+(?:more|less|increase|raise|hike)\b', q_lower)

            if delta_match and any(w in q_lower for w in ["increase", "raise", "hike", "more", "decrease", "drop", "cut", "less", "add"]):
                amount = self.parse_inr_amount(delta_match.group(1))
                if amount and amount >= Decimal("1000"):
                    if is_monthly:
                        amount = amount * Decimal("12")
                    amount_val = amount * multiplier
                    return ScenarioExtractionResult(
                        is_scenario=True,
                        scenario_type=ScenarioType.SALARY_CHANGE,
                        change_type=ChangeType.ABSOLUTE,
                        change_amount=amount_val,
                        raw_query=query,
                        description=f"Salary absolute delta of {amount_val:+,} INR"
                    )

            # Case C: Explicit Set Value (e.g. "if i earn 1 lakh per month", "salary is ₹18 lakhs", "what if salary becomes 20L", "tax on 15 LPA", "what is tax for 10 lakhs")
            val_match = re.search(r'(?:earn|earns|make|makes|making|income|salary|package|ctc|tax\s+on|tax\s+for|tax\s+if|is|becomes|of)?\s*(?:a\s+)?(?:₹|rs\.?)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|lacs?|lac|l|crores?|cr|k)?)\s*(?:per\s+month|a\s+month|monthly|per\s+year|a\s+year|annually|per\s+annum|lpa)?', q_lower)
            if val_match:
                parsed_amount = self.parse_inr_amount(val_match.group(1))
                if parsed_amount and parsed_amount >= Decimal("5000"):
                    if is_monthly and parsed_amount <= Decimal("2000000"):
                        # Convert monthly salary to annual salary (e.g. 1 lakh/month -> 12 lakhs/year)
                        annual_target = parsed_amount * Decimal("12")
                        desc = f"Salary set to ₹{parsed_amount:,}/month (₹{annual_target:,}/year)"
                    else:
                        annual_target = parsed_amount
                        desc = f"Salary set directly to ₹{annual_target:,}/year"

                    return ScenarioExtractionResult(
                        is_scenario=True,
                        scenario_type=ScenarioType.SALARY_CHANGE,
                        change_type=ChangeType.SET_VALUE,
                        target_value=annual_target,
                        raw_query=query,
                        description=desc
                    )

        # Baseline query (No scenario detected)
        return ScenarioExtractionResult(is_scenario=False, raw_query=query, description="Baseline factual query")


# Pure Python Deterministic Application Helpers

def apply_salary_scenario(baseline_annual_salary: Decimal, extraction: ScenarioExtractionResult) -> Tuple[Decimal, Decimal, str]:
    """
    Computes scenario annual salary in Python Decimal without mutating baseline.
    Returns: (scenario_annual_salary, delta_amount, human_readable_description)
    """
    if not extraction.is_scenario or extraction.scenario_type != ScenarioType.SALARY_CHANGE:
        return baseline_annual_salary, Decimal("0"), "Baseline Salary"

    if extraction.change_type == ChangeType.ABSOLUTE and extraction.change_amount is not None:
        scenario_salary = max(Decimal("0"), baseline_annual_salary + extraction.change_amount)
        delta = scenario_salary - baseline_annual_salary
        desc = f"{delta:+,.2f} INR (Absolute Change)"
        return scenario_salary, delta, desc

    elif extraction.change_type == ChangeType.PERCENTAGE and extraction.change_percentage is not None:
        pct_factor = Decimal("1") + (extraction.change_percentage / Decimal("100"))
        scenario_salary = max(Decimal("0"), (baseline_annual_salary * pct_factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        delta = scenario_salary - baseline_annual_salary
        desc = f"{extraction.change_percentage:+}% ({delta:+,.2f} INR)"
        return scenario_salary, delta, desc

    elif extraction.change_type == ChangeType.SET_VALUE and extraction.target_value is not None:
        scenario_salary = max(Decimal("0"), extraction.target_value)
        delta = scenario_salary - baseline_annual_salary
        desc = f"Directly set to ₹{scenario_salary:,.2f} ({delta:+,.2f} INR)"
        return scenario_salary, delta, desc

    return baseline_annual_salary, Decimal("0"), "Baseline Salary"


scenario_extractor = ScenarioExtractor()
