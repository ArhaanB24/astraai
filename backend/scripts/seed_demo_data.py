import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from decimal import Decimal
from app.core.database import SessionLocal, engine, Base
from app.models import User, FinancialProfile, FundPortfolio, FundTransaction, MutualFund
from app.services.auth_service import AuthService
from app.providers.mutual_funds.mfapi import MFAPIProvider

# Authoritative Canonical Scheme Metadata
CANONICAL_SCHEMES = [
    {
        "code": "122639",
        "expected_name": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
        "fund_house": "PPFAS Mutual Fund",
        "category": "Equity Scheme - Flexi Cap Fund",
        "monthly_sip": 10000.0
    },
    {
        "code": "119063",
        "expected_name": "HDFC Nifty 50 Index Fund - Direct Plan",
        "fund_house": "HDFC Mutual Fund",
        "category": "Other Scheme - Index Funds",
        "monthly_sip": 5000.0
    },
    {
        "code": "120503",
        "expected_name": "Axis ELSS Tax Saver Fund - Direct Plan - Growth Option",
        "fund_house": "Axis Mutual Fund",
        "category": "Equity Scheme - ELSS",
        "monthly_sip": 5000.0
    }
]


def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    provider = MFAPIProvider()

    # 1. Create or get Demo User
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

    # 2. Create Financial Profile
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user.id).first()
    if not profile:
        profile = FinancialProfile(
            user_id=user.id,
            age=28,
            employment_type="Salaried",
            dependents=1,
            city_tier="Tier 1",
            monthly_salary=120000.0,
            monthly_expenses=45000.0,
            monthly_emi=15000.0,
            bank_balance=250000.0,
            existing_investments=450000.0,
            risk_tolerance="Aggressive",
            investment_horizon_years=7
        )
        db.add(profile)
        db.commit()

    # 3. Create Portfolio
    portfolio = db.query(FundPortfolio).filter(FundPortfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = FundPortfolio(user_id=user.id, name="Capstone SIP Portfolio")
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)

    # Clear existing transactions to re-seed cleanly with exact canonical schemes & real historical NAVs
    db.query(FundTransaction).filter(FundTransaction.portfolio_id == portfolio.id).delete()
    db.commit()

    today = datetime.utcnow().date()

    for scheme_info in CANONICAL_SCHEMES:
        code = scheme_info["code"]
        sip_amount = Decimal(str(scheme_info["monthly_sip"]))

        # Fetch authoritative details directly from AMFI provider
        details = provider.get_fund_details(code)
        history = provider.get_nav_history(code, limit=400)

        canonical_name = details["scheme_name"] if details else scheme_info["expected_name"]
        fund_house = details.get("fund_house") if details else scheme_info["fund_house"]
        category = details.get("category") if details else scheme_info["category"]
        current_nav = details.get("current_nav") if details else None

        db_fund = db.query(MutualFund).filter(MutualFund.scheme_code == code).first()
        if not db_fund:
            db_fund = MutualFund(
                scheme_code=code,
                scheme_name=canonical_name,
                fund_house=fund_house,
                category=category,
                current_nav=current_nav
            )
            db.add(db_fund)
            db.commit()
            db.refresh(db_fund)
        else:
            db_fund.scheme_name = canonical_name
            db_fund.fund_house = fund_house
            db_fund.category = category
            db_fund.current_nav = current_nav
            db.commit()

        nav_map = {}
        for entry in history:
            try:
                d_obj = datetime.strptime(entry["date"], "%d-%m-%Y").date()
                nav_map[d_obj] = Decimal(str(entry["nav"]))
            except Exception:
                continue

        sorted_dates = sorted(nav_map.keys())
        if not sorted_dates:
            continue

        # Seed 12 monthly SIPs using exact historical NAV from AMFI
        for m in range(12, 0, -1):
            year = today.year if today.month - m > 0 else today.year - 1
            month = (today.month - m) % 12
            if month == 0:
                month = 12

            target_date = datetime(year, month, 15).date()
            closest_date = None
            for d in sorted_dates:
                if d <= target_date:
                    closest_date = d
                else:
                    break

            if not closest_date:
                closest_date = sorted_dates[0]

            actual_nav_dec = nav_map[closest_date]
            units_dec = sip_amount / actual_nav_dec
            tx_dt = datetime.combine(closest_date, datetime.min.time())

            tx = FundTransaction(
                user_id=user.id,
                portfolio_id=portfolio.id,
                fund_id=db_fund.id,
                transaction_type="SIP",
                transaction_date=tx_dt,
                units=float(units_dec),
                nav=float(actual_nav_dec),
                amount=float(sip_amount)
            )
            db.add(tx)

    db.commit()
    print("Successfully seeded canonical schemes with Decimal precision & real AMFI NAVs!")


if __name__ == "__main__":
    seed_demo_data()
