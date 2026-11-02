import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine, Base
from app.models import User, FinancialProfile, IncomeSource, ExpenseItem, AssetItem, LiabilityItem, FinancialGoal
from app.services.auth_service import AuthService


def seed_personal_finance_demo():
    db = SessionLocal()

    # Add missing columns to financial_profiles if sqlite DB exists
    try:
        db.execute(text("ALTER TABLE financial_profiles ADD COLUMN emergency_fund_balance FLOAT DEFAULT 270000.0"))
    except Exception:
        pass

    try:
        db.execute(text("ALTER TABLE financial_profiles ADD COLUMN target_emergency_months INTEGER DEFAULT 6"))
    except Exception:
        pass

    db.commit()

    Base.metadata.create_all(bind=engine)

    # 1. Get or Create Demo User
    user = db.query(User).filter(User.email == "demo@arthaai.com").first()
    if not user:
        user = User(
            email="demo@arthaai.com",
            hashed_password=AuthService.get_password_hash("demo123"),
            full_name="Alex Sharma"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. Get or Create Financial Profile
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if not profile:
        profile = FinancialProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # Update profile fields
    profile.monthly_salary = 120000.0
    profile.other_monthly_income = 10000.0
    profile.monthly_expenses = 45000.0
    profile.monthly_emi = 15000.0
    profile.bank_balance = 250000.0
    profile.existing_investments = 450000.0
    profile.emergency_fund_balance = 270000.0
    profile.target_emergency_months = 6
    profile.risk_tolerance = "Moderate"
    db.commit()

    # Clear existing itemized rows for clean re-seeding
    db.query(IncomeSource).filter(IncomeSource.profile_id == profile.id).delete()
    db.query(ExpenseItem).filter(ExpenseItem.profile_id == profile.id).delete()
    db.query(AssetItem).filter(AssetItem.profile_id == profile.id).delete()
    db.query(LiabilityItem).filter(LiabilityItem.profile_id == profile.id).delete()
    db.query(FinancialGoal).filter(FinancialGoal.profile_id == profile.id).delete()
    db.commit()

    # Income Sources
    incomes = [
        IncomeSource(profile_id=profile.id, name="Primary Salary (Tech Corp)", category="Salary", amount=120000.0, frequency="Monthly"),
        IncomeSource(profile_id=profile.id, name="Freelance / Consulting", category="Business", amount=10000.0, frequency="Monthly")
    ]
    db.add_all(incomes)

    # Expenses
    expenses = [
        ExpenseItem(profile_id=profile.id, name="Apartment Rent & Society", category="Essential", amount=22000.0, is_essential=True),
        ExpenseItem(profile_id=profile.id, name="Groceries & Household Supplies", category="Essential", amount=12000.0, is_essential=True),
        ExpenseItem(profile_id=profile.id, name="Electricity, Internet & Utilities", category="Essential", amount=5000.0, is_essential=True),
        ExpenseItem(profile_id=profile.id, name="Dining Out & Entertainment", category="Discretionary", amount=6000.0, is_essential=False)
    ]
    db.add_all(expenses)

    # Assets
    assets = [
        AssetItem(profile_id=profile.id, name="HDFC Savings Account (Emergency Buffer)", category="Liquid", amount=270000.0, liquidity_tier="High"),
        AssetItem(profile_id=profile.id, name="Mutual Fund Equity Portfolio", category="Equity", amount=239955.70, liquidity_tier="High"),
        AssetItem(profile_id=profile.id, name="Fixed Deposits (ICICI Bank)", category="Fixed Income", amount=210044.30, liquidity_tier="Medium")
    ]
    db.add_all(assets)

    # Liabilities
    liabilities = [
        LiabilityItem(profile_id=profile.id, name="Existing Personal Loan", category="Personal Loan", principal_outstanding=450000.0, monthly_emi=15000.0, interest_rate_pct=11.5, tenure_months_left=36)
    ]
    db.add_all(liabilities)

    # Goals
    goals = [
        FinancialGoal(profile_id=profile.id, name="House Down Payment", target_amount=2500000.0, current_amount=450000.0, target_year=2030, expected_return_pct=10.0, priority="High"),
        FinancialGoal(profile_id=profile.id, name="International Vacation", target_amount=300000.0, current_amount=100000.0, target_year=2027, expected_return_pct=7.0, priority="Medium")
    ]
    db.add_all(goals)

    db.commit()
    print("Successfully seeded Personal Finance Shared Profile for Alex Sharma!")
    db.close()


if __name__ == "__main__":
    seed_personal_finance_demo()
