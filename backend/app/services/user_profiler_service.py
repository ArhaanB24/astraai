import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import FinancialProfile, FinancialGoal
from app.models.user_questionnaire import UserQuestionnaire
from app.core.currency import format_inr

logger = logging.getLogger(__name__)


class UserProfilerService:
    """
    User Intelligence & Personalization Engine for ArthaAI.
    
    Extracts, synthesizes, and maintains a comprehensive 360-degree Financial Dossier
    and Personalized Advisor Briefing from the user's questionnaire, financial profile,
    portfolio, and behavioral metrics.
    
    This dossier is injected directly into each RAG agent (Personal Finance, Tax, Mutual Funds),
    ensuring all recommendations are hyper-tailored to the user's exact life stage, income,
    dependents, debt commitments, tax regime, and psychological loss tolerance.
    """

    @classmethod
    def get_user_dossier(cls, db: Session, user_id: str) -> Dict[str, Any]:
        """
        Builds a comprehensive structured user dossier dictionary.
        """
        user = db.query(User).filter(User.id == user_id).first()
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
        q_entries = db.query(UserQuestionnaire).filter(UserQuestionnaire.user_id == user_id).all()
        q_dict = {q.question_key: q.answer for q in q_entries}

        full_name = getattr(user, "full_name", "") or q_dict.get("full_name") or "Investor"
        age = int(getattr(profile, "age", 0) or q_dict.get("age", 28) or 28)
        employment_type = getattr(profile, "employment_type", "") or q_dict.get("employment_type", "Salaried")
        city_tier = getattr(profile, "city_tier", "") or q_dict.get("city_tier", "Tier 1 Metro")
        dependents = int(getattr(profile, "dependents", 0) or q_dict.get("dependents", 1) or 1)

        # Cash flow dynamics
        monthly_salary = float(getattr(profile, "monthly_salary", 0.0) or q_dict.get("monthly_salary", 0.0) or 0.0)
        other_monthly_income = float(getattr(profile, "other_monthly_income", 0.0) or q_dict.get("other_monthly_income", 0.0) or 0.0)
        income_stability = q_dict.get("income_stability", "Very Stable (Fixed Monthly)")
        total_monthly_inflow = monthly_salary + other_monthly_income
        total_annual_inflow = total_monthly_inflow * 12.0

        # Outflows & Debt
        monthly_expenses = float(getattr(profile, "monthly_expenses", 0.0) or q_dict.get("monthly_expenses", 0.0) or 0.0)
        discretionary_expenses = float(q_dict.get("discretionary_expenses", 0.0) or 0.0)
        monthly_emi = float(getattr(profile, "monthly_emi", 0.0) or q_dict.get("monthly_emi", 0.0) or 0.0)
        debt_types = q_dict.get("debt_types", "None (Debt-Free)")
        total_monthly_outflow = monthly_expenses + monthly_emi

        monthly_surplus = max(0.0, total_monthly_inflow - total_monthly_outflow)
        savings_rate_pct = round((monthly_surplus / total_monthly_inflow) * 100.0, 1) if total_monthly_inflow > 0 else 0.0

        # Debt-to-income (DTI)
        dti_ratio_pct = round((monthly_emi / total_monthly_inflow) * 100.0, 1) if total_monthly_inflow > 0 else 0.0
        dti_risk_category = "Safe" if dti_ratio_pct <= 30 else ("Elevated" if dti_ratio_pct <= 50 else "High Risk")

        # Safety Net & Resilience
        emergency_fund = float(getattr(profile, "emergency_fund_balance", 0.0) or q_dict.get("emergency_fund", 0.0) or 0.0)
        target_emergency_months = int(getattr(profile, "target_emergency_months", 0) or q_dict.get("target_emergency_months", 6) or 6)
        emergency_runway_months = round(emergency_fund / total_monthly_outflow, 1) if total_monthly_outflow > 0 else 0.0
        emergency_adequacy = "Strong" if emergency_runway_months >= target_emergency_months else ("Adequate" if emergency_runway_months >= 3 else "Vulnerable")
        insurance_health = q_dict.get("insurance_health", "Standard Coverage")
        insurance_term = q_dict.get("insurance_term", "Basic Cover")

        # Existing Wealth & Assets
        existing_investments_val = float(getattr(profile, "existing_investments", 0.0) or q_dict.get("existing_investment_amount", 0.0) or 0.0)
        existing_investments_held = q_dict.get("existing_investments", "Mutual Funds")

        # Risk Profile & Behavioral Loss Tolerance
        risk_tolerance = getattr(profile, "risk_tolerance", "") or q_dict.get("risk_tolerance", "Moderate")
        market_drop_reaction = q_dict.get("market_drop_reaction", "Disciplined Compounder")
        investment_experience = q_dict.get("investment_experience", "Intermediate")

        # Calibrated Investor Persona
        if risk_tolerance == "Aggressive":
            persona = "High-Growth Wealth Maximizer" if "Opportunistic" in market_drop_reaction else "Aggressive Capital Builder"
        elif risk_tolerance == "Conservative":
            persona = "Conservative Capital Preserver"
        else:
            persona = "Disciplined Long-Term Compounder"

        # Goals & Horizon
        goals = db.query(FinancialGoal).filter(FinancialGoal.profile_id == getattr(profile, "id", "")).all() if profile else []
        primary_goal = goals[0].name if goals else (q_dict.get("primary_goal") or "Wealth Creation")
        investment_horizon = q_dict.get("investment_horizon", f"{getattr(profile, 'investment_horizon_years', 5)} Years")
        target_monthly_sip = float(q_dict.get("target_monthly_sip", 0.0) or (monthly_surplus * 0.5 if monthly_surplus > 0 else 10000.0))

        # Tax & Strategy
        tax_regime = q_dict.get("tax_regime", "New Tax Regime (Section 115BAC)")
        section_80c_status = q_dict.get("section_80c_status", "Partially Utilized")
        financial_preferences = q_dict.get("financial_preferences", "Disciplined passive compounding with tax optimization.")

        # Metro flag for HRA calculation (50% in Delhi, Mumbai, Kolkata, Chennai; 40% elsewhere)
        is_metro = any(city in city_tier.lower() for city in ["mumbai", "delhi", "metro", "tier 1", "bengaluru", "kolkata", "chennai"])

        return {
            "user_id": user_id,
            "full_name": full_name,
            "age": age,
            "career_stage": "Early Career" if age < 30 else ("Peak Accumulation" if age <= 45 else "Pre-Retirement"),
            "employment_type": employment_type,
            "city_tier": city_tier,
            "is_metro_city": is_metro,
            "dependents": dependents,
            "monthly_salary": monthly_salary,
            "other_monthly_income": other_monthly_income,
            "total_monthly_inflow": total_monthly_inflow,
            "total_annual_inflow": total_annual_inflow,
            "income_stability": income_stability,
            "monthly_expenses": monthly_expenses,
            "discretionary_expenses": discretionary_expenses,
            "monthly_emi": monthly_emi,
            "debt_types": debt_types,
            "total_monthly_outflow": total_monthly_outflow,
            "monthly_surplus": monthly_surplus,
            "savings_rate_pct": savings_rate_pct,
            "dti_ratio_pct": dti_ratio_pct,
            "dti_risk_category": dti_risk_category,
            "emergency_fund_balance": emergency_fund,
            "target_emergency_months": target_emergency_months,
            "emergency_runway_months": emergency_runway_months,
            "emergency_adequacy": emergency_adequacy,
            "insurance_health": insurance_health,
            "insurance_term": insurance_term,
            "existing_investments_valuation": existing_investments_val,
            "existing_investments_held": existing_investments_held,
            "risk_tolerance": risk_tolerance,
            "market_drop_reaction": market_drop_reaction,
            "investment_experience": investment_experience,
            "calibrated_investor_persona": persona,
            "primary_goal": primary_goal,
            "investment_horizon": investment_horizon,
            "target_monthly_sip": target_monthly_sip,
            "tax_regime": tax_regime,
            "section_80c_status": section_80c_status,
            "financial_preferences": financial_preferences,
        }

    @classmethod
    def generate_personalized_briefing_prompt(cls, db: Session, user_id: str, agent_domain: str = "general") -> str:
        """
        Produces a concise, rich markdown briefing text formatted for inclusion
        directly into LLM system prompts or grounding payloads.
        """
        d = cls.get_user_dossier(db, user_id)

        inflow_str = f"{format_inr(d['monthly_salary'])} salary"
        if d['other_monthly_income'] > 0:
            inflow_str += f" + {format_inr(d['other_monthly_income'])} secondary"

        briefing = f"""
[AUTHENTICATED USER PERSONAL FINANCIAL DOSSIER]
• Identity: {d['full_name']} | Age: {d['age']} ({d['career_stage']}) | City: {d['city_tier']} | Dependents: {d['dependents']}
• Employment: {d['employment_type']} (Income Stability: {d['income_stability']})
• Cash Flow: Inflow: {inflow_str} (Annual: {format_inr(d['total_annual_inflow'])})
• Outflow & Debt: Living Expenses: {format_inr(d['monthly_expenses'])}/mo | EMIs: {format_inr(d['monthly_emi'])}/mo ({d['debt_types']})
• Solvency & Surplus: Monthly Free Cash Flow: {format_inr(d['monthly_surplus'])}/mo (Savings Rate: {d['savings_rate_pct']}%) | DTI: {d['dti_ratio_pct']}% ({d['dti_risk_category']})
• Safety Cushion: Emergency Fund: {format_inr(d['emergency_fund_balance'])} ({d['emergency_runway_months']} mos runway vs {d['target_emergency_months']} mos target | Status: {d['emergency_adequacy']})
• Insurance Protection: Health: {d['insurance_health']} | Term Life: {d['insurance_term']}
• Wealth & Holdings: Current Portfolio: {format_inr(d['existing_investments_valuation'])} in [{d['existing_investments_held']}]
• Risk & Behavioral DNA: {d['calibrated_investor_persona']} (Self-Assessed: {d['risk_tolerance']} | Experience: {d['investment_experience']})
• Market Crash Reaction: "{d['market_drop_reaction']}"
• Target Milestone: {d['primary_goal']} over {d['investment_horizon']} | Planned SIP: {format_inr(d['target_monthly_sip'])}/mo
• Tax Strategy: {d['tax_regime']} | Section 80C: {d['section_80c_status']}
• User Stated Strategy & Notes: "{d['financial_preferences']}"
"""
        # Domain-specific advisory guidance
        if agent_domain == "personal_finance":
            briefing += f"""
[PERSONAL FINANCE AGENT TAILORING DIRECTIVES]:
1. Always frame vehicle, housing, or discretionary affordability in the context of their monthly surplus of {format_inr(d['monthly_surplus'])}, their current DTI of {d['dti_ratio_pct']}%, and their {d['dependents']} dependents.
2. Emphasize their emergency cushion ({d['emergency_runway_months']} months) and whether major purchases will deplete their safety net below their {d['target_emergency_months']} months target.
3. Align goal compoundings with their target monthly SIP capacity of {format_inr(d['target_monthly_sip'])}.
"""
        elif agent_domain == "tax":
            briefing += f"""
[TAX AGENT TAILORING DIRECTIVES]:
1. The user's active regime preference is: {d['tax_regime']}. Always check if their deductions ({d['section_80c_status']}, Health Insurance: {d['insurance_health']}) make the Old Regime or New Regime (Section 115BAC) mathematically superior for their annual income of {format_inr(d['total_annual_inflow'])}.
2. Note that user resides in a {d['city_tier']} (Metro HRA limit: {'50%' if d['is_metro_city'] else '40%'}).
3. Reference their actual tax preferences and deduction readiness in your advice.
"""
        elif agent_domain == "mutual_fund":
            briefing += f"""
[MUTUAL FUND AGENT TAILORING DIRECTIVES]:
1. The user is a calibrated '{d['calibrated_investor_persona']}' with {d['risk_tolerance']} risk tolerance and {d['investment_horizon']} horizon.
2. Behavioral Drawdown Reaction: The user's psychological response to a 20% drop is "{d['market_drop_reaction']}". When discussing market dips, tail risk, or volatility, explicitly validate and guide this behavioral tendency (e.g. disciplining them to continue systematic SIPs or capitalize on discounts).
3. Target SIP Budget: {format_inr(d['target_monthly_sip'])}/month. When recommending fund allocations, size SIP installments around this exact planned budget.
4. Existing Assets: User holds {d['existing_investments_held']} ({format_inr(d['existing_investments_valuation'])}). Avoid redundant asset class overlap.
"""
        return briefing.strip()


user_profiler_service = UserProfilerService()
