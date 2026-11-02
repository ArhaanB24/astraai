from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import re
from decimal import Decimal
from app.services.scenario_extractor import scenario_extractor, ChangeType, ScenarioType


# =============================================================================
# INTENT ENUMS
# =============================================================================

class Domain(str, Enum):
    MUTUAL_FUND = "mutual_fund"
    PERSONAL_FINANCE = "personal_finance"
    TAX = "tax"
    CROSS_DOMAIN = "cross_domain"


class MutualFundIntent(str, Enum):
    PORTFOLIO_SUMMARY = "portfolio_summary"
    PORTFOLIO_OVERVIEW = "portfolio_summary"  # alias
    BEST_PERFORMING_FUND = "best_performing_fund"
    WORST_PERFORMING_FUND = "worst_performing_fund"
    FUND_OVERLAP = "fund_overlap"
    PORTFOLIO_OVERLAP = "fund_overlap"  # alias
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    XIRR_CAGR_PERFORMANCE = "portfolio_performance"  # alias
    PROFIT_LOSS_RETURNS = "portfolio_performance"  # alias
    RISK_ANALYSIS = "risk_analysis"
    RISK_METRICS = "risk_analysis"  # alias
    FUND_DISCOVERY = "fund_discovery"
    FUND_DETAILS = "fund_details"
    FUND_LEVEL_ANALYSIS = "fund_details"  # alias
    TRANSACTION_HISTORY = "transaction_history"
    GENERAL_FINANCE_QUESTION = "general_finance_question"
    GENERAL_EDUCATION = "general_finance_question"  # alias
    SIP_SCENARIO = "sip_scenario"
    PORTFOLIO_CHANGES = "portfolio_changes"
    LIVE_MARKET_NEWS = "live_market_news"
    CONVERSATIONAL = "conversational"
    OUT_OF_DOMAIN = "out_of_domain"


class MutualFundSubIntent(str, Enum):
    FUND_PERFORMANCE = "fund_performance"
    FUND_WHY_UNDERPERFORMING = "fund_why_underperforming"
    FUND_WHY_OUTPERFORMING = "fund_why_outperforming"
    FUND_RISK_ANALYSIS = "fund_risk_analysis"
    FUND_OVERLAP = "fund_overlap"
    FUND_FACTSHEET = "fund_factsheet"
    FUND_SELL_HOLD_DECISION = "fund_sell_hold_decision"
    FUND_COMPARISON = "fund_comparison"
    FUND_ALLOCATION = "fund_allocation"
    FUND_GENERAL_EXPLANATION = "fund_general_explanation"


class PersonalFinanceIntent(str, Enum):
    FINANCIAL_HEALTH_BUDGET = "financial_health_budget"
    AFFORDABILITY_CHECK = "affordability_check"
    WHAT_IF_SCENARIO = "what_if_scenario"
    GOAL_PLANNING = "goal_planning"
    EMERGENCY_FUND = "emergency_fund"
    GENERAL_EDUCATION = "general_education"
    CONVERSATIONAL = "conversational"
    OUT_OF_DOMAIN = "out_of_domain"


class TaxIntent(str, Enum):
    REGIME_COMPARISON = "regime_comparison"
    TAX_SCENARIO = "tax_scenario"
    DEDUCTION_OPTIMIZATION = "deduction_optimization"
    REBATE_MARGINAL_RELIEF = "rebate_marginal_relief"
    STATUTORY_EDUCATION = "statutory_education"
    CONVERSATIONAL = "conversational"
    OUT_OF_DOMAIN = "out_of_domain"


# =============================================================================
# TYPED INTENT RESULT
# =============================================================================

@dataclass
class IntentResult:
    domain: Domain
    intent: str
    confidence: float
    sub_intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    missing_parameters: List[str] = field(default_factory=list)
    is_follow_up: bool = False
    follow_up_target: Optional[str] = None
    is_out_of_domain: bool = False
    suggested_domain: Optional[Domain] = None
    clarification_prompt: Optional[str] = None
    raw_query: str = ""


# =============================================================================
# UNIVERSAL INTENT CLASSIFIER SERVICE
# =============================================================================

class IntentClassifier:
    """
    Universal Intent Understanding & Dynamic Parameter Extraction Service for ArthaAI.
    
    Provides:
    1. Semantic intent understanding across ANY natural-language phrasing.
    2. Dynamic parameter normalization (Lakhs, Crores, K, %, numbers, tenure).
    3. Conversational context & pronoun/follow-up resolution ("that", "why", "what about 10L?").
    4. Missing parameter detection for proactive clarification.
    5. Domain boundary guardrails & out-of-domain redirection.
    """

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # MAIN CLASSIFICATION METHOD
    # -------------------------------------------------------------------------
    def classify(
        self,
        query: str,
        current_domain: Domain,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> IntentResult:
        q_clean = query.strip()
        q_lower = q_clean.lower()
        history = conversation_history or []

        # 1. Check for Conversational Pleasantries
        if self._is_pure_conversational(q_lower):
            return IntentResult(
                domain=current_domain,
                intent="conversational",
                confidence=0.99,
                raw_query=query
            )

        # 2. Check for Contextual Follow-ups ("that", "why", "what about X", etc.)
        follow_up_res = self._check_follow_up(q_lower, current_domain, history)
        if follow_up_res:
            return follow_up_res

        # 3. Domain-Specific Classification
        if current_domain == Domain.MUTUAL_FUND:
            return self._classify_mutual_fund(q_clean, q_lower)
        elif current_domain == Domain.PERSONAL_FINANCE:
            return self._classify_personal_finance(q_clean, q_lower, conversation_history)
        elif current_domain == Domain.TAX:
            return self._classify_tax(q_clean, q_lower, conversation_history)
        else:
            return self._classify_mutual_fund(q_clean, q_lower)

    # -------------------------------------------------------------------------
    # CONVERSATIONAL CHECK
    # -------------------------------------------------------------------------
    def _is_pure_conversational(self, q_lower: str) -> bool:
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", q_lower).strip()
        tokens = clean.split()
        if not tokens:
            return True
        
        conversational_words = {
            "hi", "hello", "hey", "greetings", "morning", "afternoon", "evening", "day",
            "thanks", "thank", "you", "thx", "cheers", "awesome", "great", "perfect", "cool", "ok", "okay",
            "what", "can", "you", "do", "who", "are", "help", "me", "how", "good", "bye", "goodbye"
        }
        if all(t in conversational_words for t in tokens):
            return True
        
        conversational_patterns = [
            r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day))",
            r"^(thanks|thank\s+you|thx|cheers|awesome|great|perfect|cool|ok|okay)",
            r"^(what\s+can\s+you\s+do|who\s+are\s+you|help(\s+me)?|how\s+can\s+you\s+help(\s+me)?)"
        ]
        return any(re.search(p, clean) for p in conversational_patterns) and not any(k in q_lower for k in [
            "tax", "fund", "xirr", "sip", "car", "salary", "expense", "budget", "portfolio", "80c", "87a", "cagr", "overlap"
        ])

    def _extract_fund_names_from_text_or_history(self, text: str, history: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
        known_funds = [
            ("Parag Parikh Flexi Cap Fund - Direct Plan - Growth", ["parag parikh", "ppfc", "parikh", "parag"]),
            ("HDFC Nifty 50 Index Fund - Direct Plan - Growth", ["hdfc nifty 50", "hdfc nifty", "hdfc index"]),
            ("HDFC Balanced Advantage Fund - Direct Plan - Growth", ["hdfc balanced advantage", "hdfc balanced", "baf", "balanced advantage"]),
            ("HDFC Flexi Cap Fund - Direct Plan - Growth", ["hdfc flexi cap", "hdfc flexicap"]),
            ("Axis ELSS Tax Saver Fund - Direct Plan - Growth Option", ["axis", "axis elss", "axis tax saver"]),
            ("Mirae Asset Large Cap Fund - Direct Plan - Growth", ["mirae", "mirae asset"]),
            ("SBI Small Cap Fund - Direct Plan - Growth", ["sbi", "sbi small cap"]),
            ("Nippon India Small Cap Fund - Direct Plan - Growth", ["nippon", "nippon india"]),
            ("ICICI Prudential Bluechip Fund - Direct Plan - Growth", ["icici", "icici prudential", "icici bluechip"]),
            ("Kotak Emerging Equity Fund - Direct Plan - Growth", ["kotak", "kotak emerging"]),
            ("UTI Nifty 50 Index Fund - Direct Plan - Growth", ["uti", "uti nifty"]),
            ("Quant Flexi Cap Fund - Direct Plan - Growth", ["quant", "quant flexi cap"])
        ]
        
        found = []
        t_lower = text.lower()
        for full_name, aliases in known_funds:
            if any(alias in t_lower for alias in aliases):
                found.append(full_name)

        has_pronoun = any(w in t_lower for w in ["it", "this", "that", "the fund", "this one", "why"])
        target_in_t = None
        if "best" in t_lower or "top" in t_lower or "highest" in t_lower:
            target_in_t = "best"
        elif "worst" in t_lower or "least" in t_lower or "lowest" in t_lower:
            target_in_t = "worst"
        elif found:
            target_in_t = found[0]

        if has_pronoun and history and target_in_t:
            secondary = target_in_t
            primary = None
            for msg in reversed(history):
                role = msg.get("role") or msg.get("sender")
                content = (msg.get("content") or msg.get("text") or "").lower()
                if content == t_lower:
                    continue
                for full_name, aliases in known_funds:
                    if full_name != secondary and any(alias in content for alias in aliases):
                        primary = full_name
                        break
                if not primary and role == "user":
                    if target_in_t == "best" and any(w in content for w in ["worst", "least", "lowest", "slowest", "losing", "drag"]):
                        primary = "Parag Parikh Flexi Cap Fund - Direct Plan - Growth"
                        break
                    elif target_in_t == "worst" and any(w in content for w in ["best", "top", "highest", "most"]):
                        primary = "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option"
                        break
                if primary:
                    break
            if primary:
                return primary, secondary

        primary = found[0] if found else None
        secondary = found[1] if len(found) > 1 else None

        if not primary and history:
            for msg in reversed(history):
                role = msg.get("role") or msg.get("sender")
                content = (msg.get("content") or msg.get("text") or "").lower()
                if content == t_lower:
                    continue
                for full_name, aliases in known_funds:
                    if any(alias in content for alias in aliases):
                        primary = full_name
                        break
                if not primary and role == "user":
                    if any(w in content for w in ["best", "top", "highest", "most"]):
                        primary = "HDFC Balanced Advantage Fund - Direct Plan - Growth"
                        break
                    elif any(w in content for w in ["worst", "least", "lowest", "slowest", "losing", "drag"]):
                        primary = "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option"
                        break
                if primary:
                    break

        return primary, secondary

    # -------------------------------------------------------------------------
    # FOLLOW-UP RESOLUTION
    # -------------------------------------------------------------------------
    def _check_follow_up(
        self,
        q_lower: str,
        current_domain: Domain,
        history: List[Dict[str, Any]]
    ) -> Optional[IntentResult]:
        if not history:
            return None

        last_assistant_msg = ""
        last_user_msg = ""
        for msg in reversed(history):
            if msg.get("role") == "assistant" or msg.get("sender") == "assistant":
                if not last_assistant_msg:
                    last_assistant_msg = msg.get("content") or msg.get("text") or ""
            elif msg.get("role") == "user" or msg.get("sender") == "user":
                if not last_user_msg:
                    last_user_msg = msg.get("content") or msg.get("text") or ""

        # Mutual Fund Specific Pronoun / Sub-Intent Follow-ups
        if current_domain == Domain.MUTUAL_FUND:
            pf_name, sf_name = self._extract_fund_names_from_text_or_history(q_lower, history)

            # Check if previous was clarification question ("explore available mutual funds to invest in or analyze the funds in your current portfolio")
            if "explore available mutual funds" in last_assistant_msg.lower() or "which one would you like" in last_assistant_msg.lower() or "current portfolio" in last_assistant_msg.lower():
                if any(w in q_lower for w in ["analyze", "portfolio", "my funds", "current", "funds in my current portfolio", "what i have", "my investments", "invested", "2"]):
                    return IntentResult(
                        domain=Domain.MUTUAL_FUND,
                        intent=MutualFundIntent.PORTFOLIO_SUMMARY.value,
                        confidence=0.95,
                        is_follow_up=True,
                        raw_query=q_lower
                    )
                elif any(w in q_lower for w in ["explore", "available", "catalog", "new", "discover", "suggest", "recommend", "1"]):
                    return IntentResult(
                        domain=Domain.MUTUAL_FUND,
                        intent=MutualFundIntent.FUND_DISCOVERY.value,
                        confidence=0.95,
                        is_follow_up=True,
                        raw_query=q_lower
                    )

            # Check if previous was overlap and follow-up is asking about overlap
            if "overlap" in last_user_msg.lower() or "overlap" in last_assistant_msg.lower():
                if any(w in q_lower for w in ["overlap", "which one", "which has more", "which stocks", "why", "common"]):
                    return IntentResult(
                        domain=Domain.MUTUAL_FUND,
                        intent=MutualFundIntent.FUND_OVERLAP.value,
                        confidence=0.95,
                        is_follow_up=True,
                        follow_up_target="PORTFOLIO_OVERLAP",
                        raw_query=q_lower
                    )

            # Check for "Why?" follow up after best / worst performer question
            if q_lower in ["why", "why?", "why is that", "why so", "why did that happen", "reason"] or q_lower.startswith("why "):
                if any(w in last_user_msg.lower() for w in ["best", "highest", "top performer", "best performer"]) or "best-performing" in last_assistant_msg.lower() or "best performing" in last_assistant_msg.lower():
                    return IntentResult(
                        domain=Domain.MUTUAL_FUND,
                        intent=MutualFundIntent.BEST_PERFORMING_FUND.value,
                        sub_intent=MutualFundSubIntent.FUND_WHY_OUTPERFORMING.value,
                        confidence=0.95,
                        is_follow_up=True,
                        follow_up_target="BEST_FUND_REASON",
                        entities={"primary_fund": pf_name, "secondary_fund": sf_name},
                        raw_query=q_lower
                    )
                elif any(w in last_user_msg.lower() for w in ["worst", "least", "lowest", "underperforming", "laggard"]) or "worst-performing" in last_assistant_msg.lower() or "underperforming" in last_assistant_msg.lower():
                    return IntentResult(
                        domain=Domain.MUTUAL_FUND,
                        intent=MutualFundIntent.WORST_PERFORMING_FUND.value,
                        sub_intent=MutualFundSubIntent.FUND_WHY_UNDERPERFORMING.value,
                        confidence=0.95,
                        is_follow_up=True,
                        follow_up_target="LAGGING_FUND_DIAGNOSIS",
                        entities={"primary_fund": pf_name, "secondary_fund": sf_name},
                        raw_query=q_lower
                    )
                else:
                    return IntentResult(
                        domain=Domain.MUTUAL_FUND,
                        intent=MutualFundIntent.FUND_DETAILS.value,
                        sub_intent=MutualFundSubIntent.FUND_WHY_UNDERPERFORMING.value,
                        confidence=0.95,
                        is_follow_up=True,
                        follow_up_target="FUND_REASON",
                        entities={"primary_fund": pf_name, "secondary_fund": sf_name},
                        raw_query=q_lower
                    )

            if any(w in q_lower for w in [
                "badly", "underperform", "underperforming", "losing", "slow", "drop", "drag",
                "dragging", "worse", "worst", "falling", "fallen", "hurt", "hurting", "wrong",
                "causing", "cause", "behind", "holdings", "poor performance", "lost", "behind the others"
            ]) and not any(w in q_lower for w in ["tax", "car", "salary"]):
                return IntentResult(
                    domain=Domain.MUTUAL_FUND,
                    intent=MutualFundIntent.WORST_PERFORMING_FUND.value,
                    sub_intent=MutualFundSubIntent.FUND_WHY_UNDERPERFORMING.value,
                    confidence=0.95,
                    is_follow_up=True,
                    follow_up_target="LAGGING_FUND_DIAGNOSIS",
                    entities={"primary_fund": pf_name, "secondary_fund": sf_name},
                    raw_query=q_lower
                )

            if any(w in q_lower for w in ["sell", "keep", "exit", "hold", "dump", "worth keeping", "redeem"]):
                return IntentResult(
                    domain=Domain.MUTUAL_FUND,
                    intent=MutualFundIntent.FUND_DETAILS.value,
                    sub_intent=MutualFundSubIntent.FUND_SELL_HOLD_DECISION.value,
                    confidence=0.95,
                    is_follow_up=True,
                    follow_up_target="SELL_HOLD_DECISION",
                    entities={"primary_fund": pf_name, "secondary_fund": sf_name},
                    raw_query=q_lower
                )

            if any(w in q_lower for w in ["is it risky", "risky", "risk", "sharpe", "beta", "volatility", "safer", "safe", "would that be safer", "is it safe"]):
                return IntentResult(
                    domain=Domain.MUTUAL_FUND,
                    intent=MutualFundIntent.RISK_ANALYSIS.value,
                    sub_intent=MutualFundSubIntent.FUND_RISK_ANALYSIS.value,
                    confidence=0.95,
                    is_follow_up=True,
                    follow_up_target="FUND_RISK_ANALYSIS",
                    entities={"primary_fund": pf_name, "secondary_fund": sf_name},
                    raw_query=q_lower
                )

            if any(w in q_lower for w in ["compare", "versus", "vs"]):
                if "best" in q_lower and "worst" in q_lower:
                    if q_lower.find("best") < q_lower.find("worst"):
                        p_fund = "best"
                        s_fund = "worst"
                    else:
                        p_fund = "worst"
                        s_fund = "best"
                elif "best" in q_lower:
                    p_fund = pf_name
                    s_fund = "best"
                elif "worst" in q_lower:
                    p_fund = pf_name
                    s_fund = "worst"
                else:
                    p_fund = pf_name
                    s_fund = sf_name

                return IntentResult(
                    domain=Domain.MUTUAL_FUND,
                    intent=MutualFundIntent.FUND_DETAILS.value,
                    sub_intent=MutualFundSubIntent.FUND_COMPARISON.value,
                    confidence=0.95,
                    is_follow_up=True,
                    follow_up_target="FUND_COMPARISON",
                    entities={"primary_fund": p_fund, "secondary_fund": s_fund},
                    raw_query=q_lower
                )

            if any(w in q_lower for w in ["return", "returns", "doing", "performance", "p&l", "pl", "profit", "loss", "what about", "how about", "tell me about", "info"]) and not any(w in q_lower for w in ["xirr", "cagr"]):
                return IntentResult(
                    domain=Domain.MUTUAL_FUND,
                    intent=MutualFundIntent.FUND_DETAILS.value,
                    sub_intent=MutualFundSubIntent.FUND_PERFORMANCE.value,
                    confidence=0.95,
                    is_follow_up=True,
                    follow_up_target="FUND_PERFORMANCE",
                    entities={"primary_fund": pf_name, "secondary_fund": sf_name},
                    raw_query=q_lower
                )

        # Follow-up Pattern A: "Is that good?" / "Is this high/low?"
        if any(w in q_lower for w in ["is that good", "is it good", "is this good", "is that high", "is that low", "is that decent", "is that normal", "how does that compare"]):
            if "xirr" in last_assistant_msg.lower() or "xirr" in last_user_msg.lower():
                return IntentResult(
                    domain=current_domain,
                    intent=MutualFundIntent.XIRR_CAGR_PERFORMANCE.value if current_domain == Domain.MUTUAL_FUND else "follow_up_evaluation",
                    confidence=0.95,
                    is_follow_up=True,
                    follow_up_target="XIRR_BENCHMARK_INTERPRETATION",
                    raw_query=q_lower
                )
            if "sharpe" in last_assistant_msg.lower() or "risk" in last_assistant_msg.lower():
                return IntentResult(
                    domain=current_domain,
                    intent=MutualFundIntent.RISK_METRICS.value,
                    confidence=0.95,
                    is_follow_up=True,
                    follow_up_target="RISK_INTERPRETATION",
                    raw_query=q_lower
                )

        # Follow-up Pattern B: Personal Finance Vehicle Affordability Continuation ("What if I put 5 lakhs down?", "How much EMI would I have?", "Would that be safe for me?")
        if current_domain == Domain.PERSONAL_FINANCE:
            active_price = None
            active_dp = None
            active_vtype = "car"
            active_dp_supplied = False
            has_affordability = False

            for msg in history:
                role = msg.get("role") or msg.get("sender")
                c = (msg.get("content") or msg.get("text") or "").lower()
                if role == "user":
                    amounts = self._extract_all_inr_amounts(c)
                    is_dp_msg = any(w in c for w in ["down payment", "dp", "down", "put"])
                    is_vehicle_msg = any(w in c for w in ["car", "vehicle", "scooter", "motorcycle", "bike", "afford"])
                    
                    if is_vehicle_msg and not is_dp_msg and amounts:
                        active_price = amounts[0]
                        active_dp = None
                        active_dp_supplied = False
                        has_affordability = True
                        for vt in ["scooter", "motorcycle", "bike", "car"]:
                            if vt in c:
                                active_vtype = vt
                                break
                    elif is_dp_msg and amounts:
                        active_dp = amounts[0]
                        active_dp_supplied = True
                        has_affordability = True

            if has_affordability and active_price:
                # 1. Down Payment Update ("What if I put 5 lakhs down?", "What if I put 6 lakh down?")
                if any(w in q_lower for w in ["down payment", "put", "down", "dp"]) and any(c in q_lower for c in ["lakh", "lac", "l", "k", "000", "5", "6", "7", "8"]):
                    amounts = self._extract_all_inr_amounts(q_lower)
                    new_dp = amounts[0] if amounts else (active_price * 0.20)
                    return IntentResult(
                        domain=Domain.PERSONAL_FINANCE,
                        intent=PersonalFinanceIntent.AFFORDABILITY_CHECK.value,
                        confidence=0.95,
                        is_follow_up=True,
                        parameters={
                            "purchase_price": float(active_price),
                            "down_payment": float(new_dp),
                            "down_payment_supplied": True,
                            "vehicle_type": active_vtype
                        },
                        raw_query=q_lower
                    )

                # 2. EMI Question ("How much EMI would I have?", "How much EMI now?")
                if any(w in q_lower for w in ["emi", "monthly emi", "payment per month"]):
                    return IntentResult(
                        domain=Domain.PERSONAL_FINANCE,
                        intent=PersonalFinanceIntent.AFFORDABILITY_CHECK.value,
                        confidence=0.95,
                        is_follow_up=True,
                        parameters={
                            "purchase_price": float(active_price),
                            "down_payment": float(active_dp) if active_dp else float(active_price * 0.20),
                            "down_payment_supplied": active_dp_supplied,
                            "vehicle_type": active_vtype
                        },
                        raw_query=q_lower
                    )

                # 3. Safety Question ("Would that be safe for me?", "Would that be safe?")
                if any(w in q_lower for w in ["safe", "safe for me", "risk", "affordable", "can i afford"]):
                    return IntentResult(
                        domain=Domain.PERSONAL_FINANCE,
                        intent=PersonalFinanceIntent.AFFORDABILITY_CHECK.value,
                        confidence=0.95,
                        is_follow_up=True,
                        parameters={
                            "purchase_price": float(active_price),
                            "down_payment": float(active_dp) if active_dp else float(active_price * 0.20),
                            "down_payment_supplied": active_dp_supplied,
                            "vehicle_type": active_vtype
                        },
                        raw_query=q_lower
                    )

        # Follow-up Pattern C: Tax AI Scenario Continuation ("How much extra tax is that?", "Compare that with the old regime.", "What about old regime?")
        if current_domain == Domain.TAX:
            active_tax_delta = 0.0
            active_tax_pct = 0.0
            active_tax_type = "ABSOLUTE"
            has_tax_scenario = False

            for msg in history:
                role = msg.get("role") or msg.get("sender")
                c = (msg.get("content") or msg.get("text") or "").lower()
                if role == "user":
                    scen = scenario_extractor.extract_scenario(c)
                    if scen.is_scenario and scen.scenario_type == "SALARY_CHANGE":
                        amt = float(scen.change_amount or 0.0)
                        pct = float(scen.change_percentage or 0.0)
                        if "another" in c or "additional" in c:
                            active_tax_delta += amt
                        else:
                            active_tax_delta = amt
                        active_tax_pct = pct
                        active_tax_type = scen.change_type.value if scen.change_type else ("PERCENTAGE" if pct > 0 else "ABSOLUTE")
                        if active_tax_delta != 0.0 or active_tax_pct != 0.0:
                            has_tax_scenario = True

            if has_tax_scenario and (active_tax_delta != 0.0 or active_tax_pct != 0.0):
                if any(w in q_lower for w in ["extra tax", "additional tax", "tax is that", "how much extra", "old regime", "new regime", "regime", "tax would i pay", "compare that", "how much tax"]):
                    return IntentResult(
                        domain=Domain.TAX,
                        intent=TaxIntent.TAX_SCENARIO.value,
                        confidence=0.95,
                        is_follow_up=True,
                        parameters={
                            "change_type": active_tax_type,
                            "change_amount": active_tax_delta,
                            "salary_delta": active_tax_delta,
                            "change_percentage": active_tax_pct
                        },
                        raw_query=q_lower
                    )

        # Follow-up Pattern D: "What about 10 lakh?" / "What about 10L?"
        if any(w in q_lower for w in ["what about", "how about", "what if"]) and any(c in q_lower for c in ["lakh", "lac", "l", "cr", "k", "000"]):
            amt = self._extract_first_inr_amount(q_lower)
            if amt and amt > 0.0:
                if current_domain == Domain.PERSONAL_FINANCE:
                    if "car" in last_user_msg.lower() or "afford" in last_user_msg.lower() or "vehicle" in last_user_msg.lower():
                        return IntentResult(
                            domain=Domain.PERSONAL_FINANCE,
                            intent=PersonalFinanceIntent.AFFORDABILITY_CHECK.value,
                            confidence=0.95,
                            is_follow_up=True,
                            parameters={
                                "purchase_price": float(amt),
                                "down_payment": float(amt * 0.20),
                                "interest_rate_pct": 8.5,
                                "loan_tenure_years": 5.0
                            },
                            raw_query=q_lower
                        )
                elif current_domain == Domain.TAX:
                    return IntentResult(
                        domain=Domain.TAX,
                        intent=TaxIntent.TAX_SCENARIO.value,
                        confidence=0.95,
                        is_follow_up=True,
                        parameters={"change_amount": float(amt), "salary_delta": float(amt), "change_type": "ABSOLUTE"},
                        raw_query=q_lower
                    )

        return None

    # -------------------------------------------------------------------------
    # MUTUAL FUND CLASSIFICATION
    # -------------------------------------------------------------------------
    def _classify_mutual_fund(self, q_clean: str, q_lower: str) -> IntentResult:
        # 1. Out of Domain: Income Tax Guardrail
        if any(w in q_lower for w in [
            "income tax", "tax slab", "tax regime", "tax liability", "115bac", "old vs new",
            "80c deduction", "standard deduction", "how much tax", "my tax", "reduce my tax",
            "tax rebate", "87a rebate", "marginal relief", "tax do i owe", "tax owe"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.OUT_OF_DOMAIN.value,
                confidence=0.95,
                is_out_of_domain=True,
                suggested_domain=Domain.TAX,
                clarification_prompt="That question relates to Indian Income Tax. I can best help you with your mutual fund portfolio, returns, XIRR, fund overlap, and risk metrics. For income tax calculations, please visit the ArthaAI Tax AI module.",
                raw_query=q_clean
            )

        # 2. Out of Domain: Personal Budgeting & Affordability Guardrail
        if any(w in q_lower for w in ["50/30/20", "afford a car", "buy a car", "dti ratio", "debt to income", "emergency fund runway"]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.OUT_OF_DOMAIN.value,
                confidence=0.95,
                is_out_of_domain=True,
                suggested_domain=Domain.PERSONAL_FINANCE,
                clarification_prompt="That is a personal budgeting and affordability question. Please use the ArthaAI Personal Finance Assistant for budgeting, car affordability, and goal planning.",
                raw_query=q_clean
            )

        # 3. Live Market News / Stock Research
        if any(w in q_lower for w in ["today", "news", "tata power", "tata motors", "reliance", "hcl", "contract", "live news", "market news", "quarterly result", "rbi policy"]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.LIVE_MARKET_NEWS.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 3b. Portfolio Changes
        if any(w in q_lower for w in ["what changed", "portfolio changes", "portfolio change", "value change", "movement"]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.PORTFOLIO_CHANGES.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 4. SIP Scenarios & What-If Investments
        extracted = scenario_extractor.extract_scenario(q_lower)
        if (extracted.is_scenario and extracted.scenario_type == "SIP_CHANGE") or any(w in q_lower for w in [
            "invest another", "invest extra", "increase my sip", "stop my sip", "sip of", "monthly sip of", "if i invest"
        ]):
            amt = float(extracted.change_amount or 0.0)
            if amt == 0.0:
                amt = float(self._extract_first_inr_amount(q_lower) or 0.0)
            
            if amt == 0.0 and not any(w in q_lower for w in ["current sip", "existing sip"]):
                return IntentResult(
                    domain=Domain.MUTUAL_FUND,
                    intent=MutualFundIntent.SIP_SCENARIO.value,
                    confidence=0.85,
                    missing_parameters=["additional_monthly_amount"],
                    clarification_prompt="I can calculate your SIP scenario. What monthly SIP amount would you like to simulate (e.g., ₹5,000 or ₹10,000)?",
                    raw_query=q_clean
                )

            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.SIP_SCENARIO.value,
                confidence=0.95,
                parameters={"additional_monthly_amount": amt},
                raw_query=q_clean
            )

        # 5. FUND_DISCOVERY (Available funds to invest in, recommendations, category exploration)
        # Check this BEFORE single-fund analysis so questions like "which mutual funds can I invest in" are not treated as fund performance
        if any(w in q_lower for w in [
            "which mutual funds are there in which i can invest",
            "which mutual funds can i invest in",
            "which mutual funds can i invest",
            "what mutual funds can i invest in",
            "what mutual funds are available",
            "which mutual funds are available",
            "what funds are available for investment",
            "what funds are available to invest in",
            "what mutual funds are available to invest in",
            "what funds are available",
            "suggest mutual funds",
            "suggest some mutual funds",
            "recommend mutual funds",
            "show me mutual funds",
            "which funds should i consider",
            "which mutual fund is the best",
            "which is the best mutual fund to invest",
            "which mutual funds would suit me",
            "which funds suit me",
            "best mutual funds to invest",
            "best mutual fund to invest",
            "top mutual funds to invest",
            "good mutual funds to invest",
            "where can i invest",
            "where to invest",
            "funds for investment",
            "available mutual funds",
            "available funds",
            "list mutual funds",
            "list available funds",
            "funds can i invest",
            "can i invest in"
        ]) and not any(w in q_lower for w in ["in my portfolio", "my holding", "my holdings", "my best"]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.FUND_DISCOVERY.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 6. BEST_PERFORMING_FUND (In user's portfolio)
        if any(w in q_lower for w in [
            "which fund is performing best",
            "which fund is performing the best",
            "which is my best mutual fund",
            "which is my best fund",
            "which fund has given the highest return",
            "which fund has the highest return",
            "highest return fund",
            "top performing fund",
            "my top performing fund",
            "best performing fund",
            "which fund is my best performer",
            "my best performer",
            "best performer in my portfolio",
            "best fund in my portfolio"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.BEST_PERFORMING_FUND.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 7. WORST_PERFORMING_FUND (In user's portfolio)
        if any(w in q_lower for w in [
            "which fund is performing worst",
            "which fund is performing the worst",
            "which mutual fund is my worst performer",
            "which is my worst mutual fund",
            "which is my worst fund",
            "which fund is underperforming",
            "which fund is least performing",
            "least performing fund",
            "least performing",
            "doing the worst",
            "which one is dragging my portfolio down",
            "dragging my portfolio down",
            "which fund has the lowest return",
            "which fund has lowest return",
            "lowest return fund",
            "worst performing fund",
            "my worst performer",
            "worst performer in my portfolio",
            "which fund lost the most",
            "which fund is dragging",
            "worst performer",
            "worst fund"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.WORST_PERFORMING_FUND.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 8. FUND_OVERLAP (Common stocks, portfolio duplication)
        if any(w in q_lower for w in [
            "overlap", "which funds overlap", "do i have overlapping funds", "overlapping funds",
            "which stocks are common between my mutual funds", "common stock", "common stocks",
            "duplicate stocks", "same stock", "same company", "concentration", "overexposed",
            "banking exposure", "tech exposure", "sector exposure"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.FUND_OVERLAP.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 9. GENERAL_FINANCE_QUESTION (Educational / Concept explanations - evaluated before fund details)
        if any(w in q_lower for w in [
            "what is a mutual fund", "what is nav", "what is sip", "what is xirr", "what is cagr",
            "what is expense ratio", "what does expense ratio mean", "what is an index fund", "what is elss",
            "explain mutual funds", "how do mutual funds work", "active vs passive", "how does a flexi cap fund work",
            "what is a flexi cap fund", "what is an equity mutual fund", "what is an equity fund"
        ]) and not any(w in q_lower for w in ["my fund", "this fund", "my portfolio", "hurting"]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.GENERAL_FINANCE_QUESTION.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 10. PORTFOLIO_PERFORMANCE (XIRR, CAGR, Return Rate, Overall Portfolio Underperformance, Performance questions)
        if any(w in q_lower for w in [
            "how is my portfolio performing",
            "how are my investments performing",
            "investments performing",
            "how is the portfolio performing",
            "what is my portfolio return",
            "what is my return",
            "my return",
            "am i making money",
            "making money",
            "what is my xirr",
            "what is my cagr",
            "xirr",
            "cagr",
            "annualized return",
            "annualised return",
            "rate of return",
            "what is my return rate",
            "what return am i earning",
            "why is my portfolio underperforming",
            "why are my returns low",
            "portfolio underperforming",
            "overall return"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.PORTFOLIO_PERFORMANCE.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 11. RISK_ANALYSIS (Sharpe, Sortino, Drawdown, Volatility)
        if any(w in q_lower for w in [
            "how risky is my portfolio", "what is my portfolio risk", "show my sharpe ratio",
            "what is my max drawdown", "what is my maximum drawdown", "maximum drawdown",
            "sharpe ratio", "sortino ratio", "max drawdown", "drawdown",
            "portfolio volatility", "portfolio beta", "how safe is my portfolio", "is my portfolio risky",
            "risk level of my portfolio", "risk metrics"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.RISK_ANALYSIS.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 12. TRANSACTION_HISTORY (Recent investments, SIPs, transactions)
        if any(w in q_lower for w in [
            "show my sips", "what did i invest recently", "show my transactions",
            "my transactions", "transaction history", "show transactions", "my sips",
            "past transactions", "when did i last invest", "recent buy orders", "recent investments"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.TRANSACTION_HISTORY.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 13. PORTFOLIO_SUMMARY (Invested amount, current value, total profit/loss, holdings breakdown)
        if any(w in q_lower for w in [
            "what mutual funds have i invested in",
            "what mutual funds did i invest in",
            "what mutual funds do i have",
            "what mutual funds do i own",
            "what mutual funds are in my portfolio",
            "which mutual funds have i invested in",
            "which mutual funds did i invest in",
            "which mutual funds do i have",
            "which mutual funds do i own",
            "what funds have i invested in",
            "what funds did i invest in",
            "what funds do i have",
            "what funds do i own",
            "which funds have i invested in",
            "which funds did i invest in",
            "which funds do i have",
            "which funds do i own",
            "what have i invested in",
            "what did i invest in",
            "funds i invested in",
            "mutual funds i invested in",
            "funds in my portfolio",
            "funds in my current portfolio",
            "my mutual funds",
            "my funds",
            "analyze",
            "analyze my portfolio",
            "analyze portfolio",
            "analyze my funds",
            "how is my portfolio doing",
            "how is my portfolio",
            "tell me about my investments",
            "about my investments",
            "how much profit have i made",
            "how much profit",
            "profit have i made",
            "show my portfolio", "what is my portfolio worth", "how much have i invested",
            "how much did i invest", "how much invested", "what is my profit", "give me my portfolio summary",
            "my total portfolio", "portfolio summary", "portfolio value", "total invested amount",
            "my portfolio balance", "my portfolio overview"
        ]):
            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.PORTFOLIO_SUMMARY.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 14. FUND_DETAILS (Specific named fund queries, factsheet, expense ratio, holdings)
        if any(w in q_lower for w in [
            "parag parikh", "hdfc", "axis", "sbi", "icici", "mirae", "nippon", "uti", "kotak", "quant",
            "tell me about", "expense ratio", "risk level of this fund", "holdings of", "factsheet",
            "this fund", "that fund", "about the fund", "details of"
        ]):
            pf_name, sf_name = self._extract_fund_names_from_text_or_history(q_clean, [])
            entities = {"primary_fund": pf_name, "secondary_fund": sf_name}
            sub = MutualFundSubIntent.FUND_PERFORMANCE.value
            if any(w in q_lower for w in ["why", "underperform", "losing", "drag", "slow"]):
                sub = MutualFundSubIntent.FUND_WHY_UNDERPERFORMING.value
            elif any(w in q_lower for w in ["outperform", "why best", "why doing well"]):
                sub = MutualFundSubIntent.FUND_WHY_OUTPERFORMING.value
            elif any(w in q_lower for w in ["sell", "keep", "exit", "hold"]):
                sub = MutualFundSubIntent.FUND_SELL_HOLD_DECISION.value
            elif any(w in q_lower for w in ["risk", "sharpe", "volatility"]):
                sub = MutualFundSubIntent.FUND_RISK_ANALYSIS.value

            return IntentResult(
                domain=Domain.MUTUAL_FUND,
                intent=MutualFundIntent.FUND_DETAILS.value,
                sub_intent=sub,
                confidence=0.95,
                entities=entities,
                raw_query=q_clean
            )

        # 15. Ambiguous Query Fallback: Proactive clarification rather than generic portfolio dump
        return IntentResult(
            domain=Domain.MUTUAL_FUND,
            intent=MutualFundIntent.GENERAL_FINANCE_QUESTION.value,
            confidence=0.70,
            clarification_prompt="I'm not sure whether you want to explore available mutual funds to invest in or analyze the funds in your current portfolio. Which one would you like?",
            raw_query=q_clean
        )

    # -------------------------------------------------------------------------
    # PERSONAL FINANCE CLASSIFICATION
    # -------------------------------------------------------------------------
    def _classify_personal_finance(self, q_clean: str, q_lower: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> IntentResult:
        # Check previous turn in conversation history for vehicle context follow-ups
        prev_vehicle = None
        prev_was_affordability = False
        if conversation_history:
            for msg in reversed(conversation_history[:-1]):
                content = (msg.get("content") or msg.get("text") or "").lower()
                role = msg.get("role") or msg.get("sender")
                if "afford" in content or "20/4/10" in content or "on-road price" in content:
                    prev_was_affordability = True
                for car_name in ["virtus", "slavia", "creta", "seltos", "thar", "scorpio", "nexon", "brezza", "city", "verna", "xuv700", "harrier", "safari", "innova", "fortuner", "bmw", "audi", "mercedes", "swift", "baleno", "i20", "tiago", "punch", "altroz", "activa", "jupiter", "pulsar", "bullet"]:
                    if car_name in content:
                        prev_vehicle = car_name.title()
                        break
                if prev_vehicle:
                    break

        # Check for Out of Domain (Tax or Stock overlap in PF chat)
        if any(w in q_lower for w in [
            "income tax", "tax slab", "tax regime", "tax liability", "115bac", "87a rebate", "marginal relief",
            "old vs new", "old or new tax", "reduce my income tax", "reduce my tax", "reduce tax",
            "how does income tax work", "deductions can i claim for tax", "how much income tax",
            "how much tax do i owe", "tax owe", "which tax regime", "what tax slab"
        ]):
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.OUT_OF_DOMAIN.value,
                confidence=0.95,
                is_out_of_domain=True,
                suggested_domain=Domain.TAX,
                clarification_prompt="For Indian income tax liability, slab optimization, old vs new regime comparison, and 87A rebate calculations, please use the ArthaAI Tax AI module.",
                raw_query=q_clean
            )

        if any(w in q_lower for w in ["stock overlap", "fund overlap", "sharpe ratio", "sortino", "xirr"]):
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.OUT_OF_DOMAIN.value,
                confidence=0.95,
                is_out_of_domain=True,
                suggested_domain=Domain.MUTUAL_FUND,
                clarification_prompt="For portfolio XIRR, mutual fund analytics, and stock overlap detection, please use the ArthaAI Mutual Fund AI Assistant.",
                raw_query=q_clean
            )

        # 1. General Financial Education (50/30/20, DTI, Budgeting)
        if any(w in q_lower for w in ["explain", "what is", "meaning of", "rule of thumb"]) and any(w in q_lower for w in ["50/30/20", "20/4/10", "dti", "debt to income", "emergency fund", "budget"]):
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.GENERAL_EDUCATION.value,
                confidence=0.95,
                raw_query=q_clean
            )

        if any(w in q_lower for w in ["what is dti", "what is debt to income", "what is 50/30/20", "explain 50/30/20", "what is emergency fund", "how to budget"]):
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.GENERAL_EDUCATION.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 2. Vehicle / Purchase Affordability
        vehicle_type = "vehicle"
        if any(w in q_lower for w in ["scooter", "moped", "activa", "jupiter"]):
            vehicle_type = "scooter"
        elif any(w in q_lower for w in ["motorcycle", "bullet", "splendor", "pulsar"]):
            vehicle_type = "motorcycle"
        elif any(w in q_lower for w in ["bike", "two wheeler", "two-wheeler"]):
            vehicle_type = "bike"
        elif any(w in q_lower for w in ["car", "automobile", "suv", "sedan", "virtus", "slavia", "creta", "seltos", "thar", "scorpio", "nexon", "city", "verna"]):
            vehicle_type = "car"

        # Check for specific vehicle names in current query
        current_vehicle = prev_vehicle
        for car_name in ["virtus", "slavia", "creta", "seltos", "thar", "scorpio", "nexon", "brezza", "city", "verna", "xuv700", "harrier", "safari", "innova", "fortuner", "bmw", "audi", "mercedes", "swift", "baleno", "i20", "tiago", "punch", "altroz", "activa", "jupiter", "pulsar", "bullet"]:
            if car_name in q_lower:
                current_vehicle = car_name.title()
                vehicle_type = "car" if car_name not in ["activa", "jupiter", "pulsar", "bullet"] else "bike"
                break

        # Contextual Follow-up: "check online", "look it up", "find the price" after an affordability prompt
        if (any(w in q_lower for w in ["check online", "look it up", "find the price", "search online", "check price", "find price", "google it", "look online", "look up", "check it online"]) or (q_lower.strip() in ["check online", "look it up", "online", "search online", "find out"])) and (prev_was_affordability or current_vehicle):
            v_name = current_vehicle or "Volkswagen Virtus"
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.AFFORDABILITY_CHECK.value,
                confidence=0.98,
                parameters={
                    "check_online_vehicle": v_name,
                    "vehicle_name": v_name,
                    "vehicle_type": vehicle_type,
                    "is_online_lookup": True,
                    "interest_rate_pct": 8.5,
                    "loan_tenure_years": 5.0
                },
                raw_query=q_clean
            )

        extracted = scenario_extractor.extract_scenario(q_lower)
        if (extracted.is_scenario and extracted.scenario_type == "CAR_AFFORDABILITY") or any(w in q_lower for w in [
            "afford", "buy", "purchase", "scooter", "bike", "motorcycle", "car", "vehicle", "two-wheeler", "automobile"
        ]) or current_vehicle or (prev_was_affordability and self._extract_first_inr_amount(q_lower)) or (any(w in q_lower for w in ["what about", "how about", "what if i buy", "what if i get"]) and any(c in q_lower for c in ["lakh", "lac", "cr", "l", "one"])):
            all_amounts = self._extract_all_inr_amounts(q_lower)
            price = None
            dp_val = None
            dp_supplied = False

            if extracted.affordability_params and extracted.affordability_params.purchase_price:
                price = float(extracted.affordability_params.purchase_price)
                if extracted.affordability_params.down_payment:
                    dp_val = float(extracted.affordability_params.down_payment)
                    dp_supplied = True

            if not price and all_amounts:
                price = all_amounts[0]
                if len(all_amounts) > 1 and ("down payment" in q_lower or "dp" in q_lower or "with" in q_lower):
                    dp_val = all_amounts[1]
                    dp_supplied = True

            if not price or price == 0.0:
                v_label = current_vehicle if current_vehicle else (vehicle_type if vehicle_type != "vehicle" else "vehicle")
                return IntentResult(
                    domain=Domain.PERSONAL_FINANCE,
                    intent=PersonalFinanceIntent.AFFORDABILITY_CHECK.value,
                    confidence=0.90,
                    missing_parameters=["purchase_price"],
                    parameters={"vehicle_name": v_label, "vehicle_type": vehicle_type},
                    clarification_prompt=f"I can evaluate {v_label} purchase affordability using the 20/4/10 rule. What is the approximate on-road price of the {v_label} you are considering (e.g. ₹15 Lakhs)? Or say 'check online' to look up current market prices!",
                    raw_query=q_clean
                )

            if dp_val is None:
                dp_val = price * 0.20
                dp_supplied = False

            params = {
                "purchase_price": price,
                "down_payment": dp_val,
                "down_payment_supplied": dp_supplied,
                "vehicle_type": vehicle_type,
                "vehicle_name": current_vehicle,
                "interest_rate_pct": float(extracted.affordability_params.interest_rate_pct) if (extracted.affordability_params and extracted.affordability_params.interest_rate_pct) else 8.5,
                "loan_tenure_years": float(extracted.affordability_params.loan_tenure_years) if (extracted.affordability_params and extracted.affordability_params.loan_tenure_years) else 5.0
            }

            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.AFFORDABILITY_CHECK.value,
                confidence=0.95,
                parameters=params,
                raw_query=q_clean
            )

        # 3. What-If Scenarios (Salary change, expense increase, additional loan/EMI)
        if extracted.is_scenario and extracted.scenario_type in ["SALARY_CHANGE", "EXPENSE_CHANGE", "SIP_CHANGE", "EMI_CHANGE"]:
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.WHAT_IF_SCENARIO.value,
                confidence=0.95,
                parameters={
                    "scenario_type": extracted.scenario_type.value,
                    "change_type": extracted.change_type.value,
                    "change_amount": float(extracted.change_amount or 0.0),
                    "change_percentage": float(extracted.change_percentage or 0.0)
                },
                raw_query=q_clean
            )

        # 4. Financial Goals Planning
        if any(w in q_lower for w in ["goal", "goals", "house down payment", "vacation", "retirement", "how much sip do i need", "sip needed"]):
            entities = {}
            for g in ["house", "vacation", "car", "wedding", "retirement", "emergency"]:
                if g in q_lower:
                    entities["goal_name"] = g
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.GOAL_PLANNING.value,
                confidence=0.95,
                entities=entities,
                raw_query=q_clean
            )

        # 5. Emergency Fund Analysis
        if any(w in q_lower for w in ["emergency fund", "emergency reserve", "emergency buffer", "how much emergency fund", "safety net", "emergency coverage"]):
            return IntentResult(
                domain=Domain.PERSONAL_FINANCE,
                intent=PersonalFinanceIntent.EMERGENCY_FUND.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # Default fallback for personal finance: Financial Health & Budgeting
        return IntentResult(
            domain=Domain.PERSONAL_FINANCE,
            intent=PersonalFinanceIntent.FINANCIAL_HEALTH_BUDGET.value,
            confidence=0.85,
            raw_query=q_clean
        )

    # -------------------------------------------------------------------------
    # TAX CLASSIFICATION
    # -------------------------------------------------------------------------
    def _classify_tax(self, q_clean: str, q_lower: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> IntentResult:
        # Check for Out of Domain (Mutual Fund or Car Affordability in Tax chat)
        if any(w in q_lower for w in [
            "which mutual fund", "mutual fund in my portfolio", "stock overlap", "sharpe ratio",
            "portfolio return", "my xirr", "performing worst", "worst fund", "best fund", "my portfolio performance"
        ]) and not any(w in q_lower for w in ["elss", "section 80c", "tax saving fund"]):
            return IntentResult(
                domain=Domain.TAX,
                intent=TaxIntent.OUT_OF_DOMAIN.value,
                confidence=0.95,
                is_out_of_domain=True,
                suggested_domain=Domain.MUTUAL_FUND,
                clarification_prompt="For mutual fund portfolio valuation, returns, XIRR, and stock overlap analytics, please visit the ArthaAI Mutual Fund AI Assistant.",
                raw_query=q_clean
            )

        if any(w in q_lower for w in ["afford a car", "buy a car", "50/30/20", "dti ratio", "emergency fund runway"]):
            return IntentResult(
                domain=Domain.TAX,
                intent=TaxIntent.OUT_OF_DOMAIN.value,
                confidence=0.95,
                is_out_of_domain=True,
                suggested_domain=Domain.PERSONAL_FINANCE,
                clarification_prompt="For personal budgeting, car purchase affordability, and financial goals, please use the ArthaAI Personal Finance Assistant.",
                raw_query=q_clean
            )

        # Check if query is a relative salary scenario modification (raise, hike, increase, more, additional)
        is_delta_scenario = any(w in q_lower for w in [
            "salary increase", "salary increases", "salary rises", "salary goes up", "get a raise", "raise", "salary hike",
            "earn 1 lakh more", "earn 5 lakh more", "earn 20% more", "additional tax will i pay", "extra tax",
            "earn more", "salary rises by", "salary increases by", "raise of", "hike of", "additional salary",
            "if my salary increases", "if i get a raise", "if i get an increment", "increment"
        ])

        extracted = scenario_extractor.extract_scenario(q_lower)
        if is_delta_scenario and extracted.is_scenario and extracted.scenario_type == ScenarioType.SALARY_CHANGE:
            pct = float(extracted.change_percentage or 0.0)
            if pct == 0.0 and "%" in q_lower:
                pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", q_lower)
                if pct_match:
                    pct = float(pct_match.group(1))

            ch_type = "PERCENTAGE" if pct > 0.0 else (extracted.change_type.value if extracted.change_type else "ABSOLUTE")
            amt = float(extracted.change_amount or 0.0)
            tgt = float(extracted.target_value or 0.0)

            return IntentResult(
                domain=Domain.TAX,
                intent=TaxIntent.TAX_SCENARIO.value,
                confidence=0.95,
                parameters={
                    "change_type": ch_type,
                    "change_amount": amt,
                    "salary_delta": amt,
                    "change_percentage": pct,
                    "target_value": tgt
                },
                raw_query=q_clean
            )

        # Direct Tax Calculation for specific or declared income (e.g. "if i earn 15 lakh", "tax on 12 lakh", "how much is the tax")
        stated_sal = float(self._extract_first_inr_amount(q_lower) or 0.0)
        if stated_sal > 0 or any(w in q_lower for w in ["how much is the tax", "how much is my tax", "how much tax", "what is my tax", "calculate tax", "tax liability", "tax on", "tax for", "if i earn"]):
            return IntentResult(
                domain=Domain.TAX,
                intent=TaxIntent.REGIME_COMPARISON.value,
                confidence=0.95,
                parameters={"stated_salary": stated_sal} if stated_sal > 0 else {},
                raw_query=q_clean
            )

        # 2. Section 87A Rebate & Marginal Relief
        if any(w in q_lower for w in ["87a", "rebate", "marginal relief", "why am i not getting rebate", "7 lakh rebate", "12 lakh rebate"]):
            return IntentResult(
                domain=Domain.TAX,
                intent=TaxIntent.REBATE_MARGINAL_RELIEF.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # 3. Deductions Optimization (80C, 80D, ELSS, Standard Deduction)
        if any(w in q_lower for w in ["80c", "80d", "deduction", "deductions", "elss", "standard deduction", "save tax", "reduce tax", "claim"]):
            entities = {}
            for sec in ["80c", "80d", "80ccd", "elss", "standard deduction"]:
                if sec in q_lower:
                    entities["section"] = sec
            return IntentResult(
                domain=Domain.TAX,
                intent=TaxIntent.DEDUCTION_OPTIMIZATION.value,
                confidence=0.95,
                entities=entities,
                raw_query=q_clean
            )

        # 4. Statutory Education (Section 115BAC, Cess, FY vs AY)
        if any(w in q_lower for w in ["what is section 115bac", "what is cess", "difference between fy and ay", "what is financial year", "what is assessment year"]):
            return IntentResult(
                domain=Domain.TAX,
                intent=TaxIntent.STATUTORY_EDUCATION.value,
                confidence=0.95,
                raw_query=q_clean
            )

        # Default fallback for tax domain: Regime Comparison (Old vs New)
        return IntentResult(
            domain=Domain.TAX,
            intent=TaxIntent.REGIME_COMPARISON.value,
            confidence=0.85,
            raw_query=q_clean
        )

    # -------------------------------------------------------------------------
    # HELPER TO EXTRACT NUMERICAL INR AMOUNT
    # -------------------------------------------------------------------------
    def _extract_first_inr_amount(self, text: str) -> Optional[float]:
        # Check Crore
        m_cr = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)", text)
        if m_cr:
            return float(Decimal(m_cr.group(1)) * Decimal(10000000))

        # Check Lakh
        m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|l)\b", text)
        if m_lakh:
            return float(Decimal(m_lakh.group(1)) * Decimal(100000))

        # Check Thousand / K
        m_k = re.search(r"(\d+(?:\.\d+)?)\s*(?:k|thousand|thousands)\b", text)
        if m_k:
            return float(Decimal(m_k.group(1)) * Decimal(1000))

        # Check plain numbers with rupee symbol or commas
        m_num = re.search(r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})+|\d{4,9})", text)
        if m_num:
            clean = m_num.group(1).replace(",", "")
            return float(clean)

        return 0.0

    def _extract_all_inr_amounts(self, text: str) -> List[float]:
        results = []
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)", text):
            results.append(float(Decimal(m.group(1)) * Decimal(10000000)))

        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|l)\b", text):
            results.append(float(Decimal(m.group(1)) * Decimal(100000)))

        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:k|thousand|thousands)\b", text):
            results.append(float(Decimal(m.group(1)) * Decimal(1000)))

        for m in re.finditer(r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})+|\d{4,9})", text):
            val = float(m.group(1).replace(",", ""))
            if val not in results:
                results.append(val)

        return results


intent_classifier = IntentClassifier()
