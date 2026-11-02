import sys
import os

backend_dir = os.path.abspath("backend")
sys.path.insert(0, backend_dir)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.profile import FinancialProfile, FinancialGoal
from app.models.user_questionnaire import UserQuestionnaire
from app.services.user_profiler_service import user_profiler_service

def test_user_profiler():
    print("Testing UserProfilerService & Personalized RAG Agent Dossier...")

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 1. Setup mock user
    user = User(
        id="user-rag-test",
        email="aarav.mehta@example.com",
        full_name="Aarav Mehta",
        hashed_password="mock",
        is_active=True,
        onboarding_completed=True
    )
    db.add(user)

    # 2. Setup financial profile
    profile = FinancialProfile(
        id="profile-rag-test",
        user_id=user.id,
        age=34,
        employment_type="Self-Employed Professional",
        city_tier="Tier 1 Metro (Mumbai)",
        dependents=3,
        monthly_salary=250000.0,
        other_monthly_income=50000.0,
        monthly_expenses=85000.0,
        monthly_emi=35000.0,
        emergency_fund_balance=750000.0,
        target_emergency_months=6,
        existing_investments=1800000.0,
        risk_tolerance="Aggressive",
        investment_horizon_years=10
    )
    db.add(profile)

    # 3. Setup goal
    goal = FinancialGoal(
        profile_id=profile.id,
        name="Early Financial Independence (FIRE)",
        target_amount=25000000.0,
        current_amount=1800000.0,
        target_year=2036,
        expected_return_pct=14.0,
        priority="High"
    )
    db.add(goal)

    # 4. Setup detailed questionnaire responses
    q_data = [
        ("full_name", "Aarav Mehta"),
        ("age", "34"),
        ("employment_type", "Self-Employed Professional"),
        ("city_tier", "Tier 1 Metro (Mumbai)"),
        ("dependents", "3"),
        ("monthly_salary", "250000"),
        ("other_monthly_income", "50000"),
        ("income_stability", "Moderate (Base + Variable)"),
        ("monthly_expenses", "85000"),
        ("monthly_emi", "35000"),
        ("debt_types", "Home Loan, Vehicle Loan"),
        ("emergency_fund", "750000"),
        ("target_emergency_months", "6"),
        ("insurance_health", "Comprehensive (Both Corporate + Floater)"),
        ("insurance_term", "Adequate (>10x Annual Income)"),
        ("existing_investment_amount", "1800000"),
        ("existing_investments", "Mutual Funds, Direct Stocks, EPF / PPF / NPS"),
        ("market_drop_reaction", "Opportunistic Buyer (Deploy surplus aggressively)"),
        ("risk_tolerance", "Aggressive"),
        ("investment_experience", "Advanced"),
        ("primary_goal", "Early Financial Independence (FIRE)"),
        ("investment_horizon", "10+ Years"),
        ("target_monthly_sip", "90000"),
        ("tax_regime", "Old Tax Regime (With 80C/80D Deductions)"),
        ("section_80c_status", "Fully Maxed Out (₹1.50 Lakh in ELSS/PPF)"),
        ("financial_preferences", "High-growth equity compounding, mid/small cap alpha, and tax efficiency.")
    ]
    for k, v in q_data:
        db.add(UserQuestionnaire(user_id=user.id, question_key=k, answer=v))

    db.commit()

    # 5. Extract User Dossier
    dossier = user_profiler_service.get_user_dossier(db, user.id)

    assert dossier["full_name"] == "Aarav Mehta"
    assert dossier["age"] == 34
    assert dossier["career_stage"] == "Peak Accumulation"
    assert dossier["total_monthly_inflow"] == 300000.0
    assert dossier["total_annual_inflow"] == 3600000.0
    assert dossier["total_monthly_outflow"] == 120000.0 # 85k exp + 35k emi
    assert dossier["monthly_surplus"] == 180000.0
    assert dossier["savings_rate_pct"] == 60.0 # 180k / 300k = 60%
    assert dossier["dti_ratio_pct"] == 11.7 # 35k / 300k = 11.66%
    assert dossier["dti_risk_category"] == "Safe"
    assert dossier["emergency_runway_months"] == 6.2 # 750k / 120k = 6.25 mos
    assert dossier["emergency_adequacy"] == "Strong"
    assert dossier["calibrated_investor_persona"] == "High-Growth Wealth Maximizer"
    assert dossier["is_metro_city"] is True
    assert dossier["target_monthly_sip"] == 90000.0

    print("[PASS] User dossier generated with 100% mathematical precision.")
    print(f"  • Persona: {dossier['calibrated_investor_persona']}")
    print(f"  • Savings Rate: {dossier['savings_rate_pct']}% (Surplus: INR {dossier['monthly_surplus']:,.2f}/mo)")
    print(f"  • Emergency Runway: {dossier['emergency_runway_months']} months vs {dossier['target_emergency_months']} months target")

    # 6. Verify Personal Finance Agent Prompt Tailoring
    pf_briefing = user_profiler_service.generate_personalized_briefing_prompt(db, user.id, "personal_finance")
    assert "PERSONAL FINANCE AGENT TAILORING DIRECTIVES" in pf_briefing
    assert "High-Growth Wealth Maximizer" in pf_briefing
    assert "1,80,000" in pf_briefing
    print("[PASS] Personal Finance tailored prompt briefing generated cleanly.")

    # 7. Verify Tax Agent Prompt Tailoring
    tax_briefing = user_profiler_service.generate_personalized_briefing_prompt(db, user.id, "tax")
    assert "TAX AGENT TAILORING DIRECTIVES" in tax_briefing
    assert "50%" in tax_briefing # Metro HRA limit
    assert "Old Tax Regime" in tax_briefing
    print("[PASS] Tax Agent tailored prompt briefing generated cleanly.")

    # 8. Verify Mutual Fund Agent Prompt Tailoring
    mf_briefing = user_profiler_service.generate_personalized_briefing_prompt(db, user.id, "mutual_fund")
    assert "MUTUAL FUND AGENT TAILORING DIRECTIVES" in mf_briefing
    assert "Opportunistic Buyer" in mf_briefing
    assert "90,000" in mf_briefing
    print("[PASS] Mutual Fund Agent tailored prompt briefing generated cleanly.")

    print("\nALL USER PROFILER & RAG TAILORING TESTS PASSED! 100% VERIFIED.")

if __name__ == "__main__":
    test_user_profiler()
