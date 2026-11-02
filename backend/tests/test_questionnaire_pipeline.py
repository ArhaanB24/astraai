import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath("backend")
sys.path.insert(0, backend_dir)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.profile import FinancialProfile, FinancialProfileSnapshot, FinancialGoal
from app.models.user_questionnaire import UserQuestionnaire
from app.schemas.questionnaire import QuestionnaireSubmission, QuestionnaireAnswer
from app.services.profile_service import ProfileService

def test_onboarding_pipeline():
    print("Testing Onboarding Questionnaire Pipeline...")

    # Set up in-memory sqlite engine
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 1. Create a test user
    user = User(
        id="test-user-123",
        email="priya.sharma@example.com",
        full_name="Priya",
        hashed_password="mock_password",
        is_active=True,
        onboarding_completed=False
    )
    db.add(user)
    db.commit()

    # 2. Build complete detailed questionnaire payload
    payload = QuestionnaireSubmission(
        full_name="Priya Sharma",
        age=29,
        employment_type="Salaried (Private / Tech)",
        city_tier="Tier 1 Metro (Mumbai, Delhi-NCR, BLR, HYD, PNQ)",
        dependents=2,
        monthly_salary=140000.0,
        other_monthly_income=20000.0,
        income_stability="Very Stable (Fixed Monthly)",
        monthly_expenses=50000.0,
        discretionary_expenses=15000.0,
        monthly_emi=20000.0,
        debt_types=["Home Loan", "Credit Card / BNPL"],
        emergency_fund=450000.0,
        target_emergency_months=6,
        insurance_health="Comprehensive (Both Corporate + Floater)",
        insurance_term="Adequate (>10x Annual Income)",
        existing_investment_amount=750000.0,
        existing_investments=["Mutual Funds", "Direct Stocks", "Fixed Deposits"],
        market_drop_reaction="Disciplined Compounder (Continue regular SIPs)",
        risk_tolerance="Moderate",
        investment_experience="Intermediate",
        primary_goal="Wealth Creation",
        investment_horizon="5–10 Years",
        target_monthly_sip=40000.0,
        tax_regime="New Tax Regime (Section 115BAC)",
        section_80c_status="Fully Maxed Out (₹1.50 Lakh in ELSS/PPF)",
        financial_preferences="Aggressive compounding with low-cost passive index funds and ELSS tax shield.",
        raw_responses=[
            QuestionnaireAnswer(question_key="full_name", answer="Priya Sharma"),
            QuestionnaireAnswer(question_key="age", answer="29"),
            QuestionnaireAnswer(question_key="employment_type", answer="Salaried (Private / Tech)"),
            QuestionnaireAnswer(question_key="city_tier", answer="Tier 1 Metro"),
            QuestionnaireAnswer(question_key="dependents", answer="2"),
            QuestionnaireAnswer(question_key="monthly_salary", answer="140000"),
            QuestionnaireAnswer(question_key="other_monthly_income", answer="20000"),
            QuestionnaireAnswer(question_key="income_stability", answer="Very Stable (Fixed Monthly)"),
            QuestionnaireAnswer(question_key="monthly_expenses", answer="65000"),
            QuestionnaireAnswer(question_key="discretionary_expenses", answer="15000"),
            QuestionnaireAnswer(question_key="monthly_emi", answer="20000"),
            QuestionnaireAnswer(question_key="debt_types", answer="Home Loan, Credit Card / BNPL"),
            QuestionnaireAnswer(question_key="emergency_fund", answer="450000"),
            QuestionnaireAnswer(question_key="target_emergency_months", answer="6"),
            QuestionnaireAnswer(question_key="insurance_health", answer="Comprehensive"),
            QuestionnaireAnswer(question_key="insurance_term", answer="Adequate"),
            QuestionnaireAnswer(question_key="existing_investment_amount", answer="750000"),
            QuestionnaireAnswer(question_key="existing_investments", answer="Mutual Funds, Direct Stocks, Fixed Deposits"),
            QuestionnaireAnswer(question_key="market_drop_reaction", answer="Disciplined Compounder"),
            QuestionnaireAnswer(question_key="risk_tolerance", answer="Moderate"),
            QuestionnaireAnswer(question_key="investment_experience", answer="Intermediate"),
            QuestionnaireAnswer(question_key="primary_goal", answer="Wealth Creation"),
            QuestionnaireAnswer(question_key="investment_horizon", answer="5–10 Years"),
            QuestionnaireAnswer(question_key="target_monthly_sip", answer="40000"),
            QuestionnaireAnswer(question_key="tax_regime", answer="New Tax Regime"),
            QuestionnaireAnswer(question_key="section_80c_status", answer="Fully Maxed Out"),
            QuestionnaireAnswer(question_key="financial_preferences", answer="Aggressive compounding")
        ]
    )

    # 3. Call ProfileService.save_questionnaire
    profile = ProfileService.save_questionnaire(db, user.id, payload)

    # 4. Assert User properties
    db.refresh(user)
    assert user.onboarding_completed is True, "user.onboarding_completed must be True"
    assert user.full_name == "Priya Sharma", f"user.full_name expected Priya Sharma, got {user.full_name}"
    print("[PASS] User onboarding status and name updated successfully.")

    # 5. Assert FinancialProfile mapped properties
    db.refresh(profile)
    assert profile.age == 29, f"Expected age 29, got {profile.age}"
    assert profile.employment_type == "Salaried (Private / Tech)", f"Unexpected employment_type: {profile.employment_type}"
    assert profile.city_tier == "Tier 1 Metro (Mumbai, Delhi-NCR, BLR, HYD, PNQ)"
    assert profile.dependents == 2
    assert float(profile.monthly_salary) == 140000.0
    assert float(profile.other_monthly_income) == 20000.0
    # Core (50000) + Discretionary (15000) = 65000
    assert float(profile.monthly_expenses) == 65000.0
    assert float(profile.monthly_emi) == 20000.0
    assert float(profile.emergency_fund_balance) == 450000.0
    assert float(profile.bank_balance) == 450000.0
    assert profile.target_emergency_months == 6
    assert float(profile.existing_investments) == 750000.0
    assert profile.risk_tolerance == "Moderate"
    assert profile.investment_horizon_years == 10
    print("[PASS] FinancialProfile fields mapped with 100% precision.")

    # 6. Assert FinancialGoal created
    goal = db.query(FinancialGoal).filter(FinancialGoal.profile_id == profile.id).first()
    assert goal is not None, "FinancialGoal should be created"
    assert goal.name == "Wealth Creation"
    assert goal.target_amount > 0
    print(f"[PASS] FinancialGoal created: {goal.name} with target amount INR {goal.target_amount:,.2f}")

    # 7. Assert Historical Snapshot created
    snapshot = db.query(FinancialProfileSnapshot).filter(FinancialProfileSnapshot.user_id == user.id).first()
    assert snapshot is not None, "FinancialProfileSnapshot should be generated"
    assert float(snapshot.monthly_income) == 160000.0
    assert float(snapshot.monthly_expenses) == 65000.0
    assert float(snapshot.total_assets) == 1200000.0 # 450000 bank + 750000 investments
    print(f"[PASS] FinancialProfileSnapshot recorded: Total Assets INR {snapshot.total_assets:,.2f}, Total Liabilities INR {snapshot.total_liabilities:,.2f}")

    # 8. Assert UserQuestionnaire key-value pairs stored
    q_entries = db.query(UserQuestionnaire).filter(UserQuestionnaire.user_id == user.id).all()
    assert len(q_entries) >= 25, f"Expected >= 25 question entries, got {len(q_entries)}"
    print(f"[PASS] {len(q_entries)} UserQuestionnaire entries saved cleanly in key-value store.")

    # 9. Assert Backward Compatibility with legacy 12-step submissions
    legacy_user = User(
        id="legacy-user-456",
        email="rahul@example.com",
        full_name="Rahul",
        hashed_password="mock",
        is_active=True,
        onboarding_completed=False
    )
    db.add(legacy_user)
    db.commit()

    legacy_payload = QuestionnaireSubmission(
        full_name="Rahul Verma",
        age=32,
        monthly_salary=80000.0,
        monthly_expenses=35000.0,
        monthly_emi=10000.0,
        emergency_fund=150000.0,
        investment_experience="Beginner",
        risk_tolerance="Conservative",
        primary_goal="Retirement",
        investment_horizon="10+ Years",
        existing_investments="Fixed Deposits",
        financial_preferences="Safe returns with capital preservation."
    )
    legacy_profile = ProfileService.save_questionnaire(db, legacy_user.id, legacy_payload)
    db.refresh(legacy_user)
    assert legacy_user.onboarding_completed is True
    assert legacy_user.full_name == "Rahul Verma"
    assert legacy_profile.age == 32
    assert legacy_profile.investment_horizon_years == 15
    print("[PASS] Backward compatibility verified: legacy 12-step payloads processed flawlessly.")

    print("\nALL ONBOARDING & COMPATIBILITY TESTS PASSED SUCCESSFULLY! 100% VERIFIED.")

if __name__ == "__main__":
    test_onboarding_pipeline()
