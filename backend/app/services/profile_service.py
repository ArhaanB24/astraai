from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.profile import FinancialProfile, FinancialProfileSnapshot, FinancialGoal
from app.models.user_questionnaire import UserQuestionnaire
from app.models.user import User
from app.schemas.profile import FinancialProfileCreate
from app.schemas.questionnaire import QuestionnaireSubmission


class ProfileService:

    @staticmethod
    def get_or_create_profile(db: Session, user_id: str) -> FinancialProfile:
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
        if not profile:
            profile = FinancialProfile(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update_profile(db: Session, user_id: str, profile_in: FinancialProfileCreate) -> FinancialProfile:
        profile = ProfileService.get_or_create_profile(db, user_id)

        # Update attributes
        for field, value in profile_in.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)

        db.commit()
        db.refresh(profile)

        # Create Historical Snapshot
        total_assets = float(profile.bank_balance or 0.0) + float(profile.existing_investments or 0.0)
        total_liabilities = float(profile.monthly_emi or 0.0) * 12.0  # approximate annual liability

        snapshot = FinancialProfileSnapshot(
            user_id=user_id,
            monthly_income=float(profile.monthly_salary or 0.0) + float(profile.other_monthly_income or 0.0),
            monthly_expenses=float(profile.monthly_expenses or 0.0),
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            profile_data_json=profile_in.model_dump()
        )
        db.add(snapshot)
        db.commit()

        return profile

    @staticmethod
    def save_questionnaire(db: Session, user_id: str, sub: QuestionnaireSubmission) -> FinancialProfile:
        # 1. Save or update structured questionnaire entries
        items_to_save = {}
        if sub.full_name is not None:
            items_to_save["full_name"] = str(sub.full_name)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            if sub.full_name is not None:
                user.full_name = sub.full_name
            user.onboarding_completed = True
        if sub.age is not None:
            items_to_save["age"] = str(sub.age)
        if sub.employment_type is not None:
            items_to_save["employment_type"] = str(sub.employment_type)
        if sub.city_tier is not None:
            items_to_save["city_tier"] = str(sub.city_tier)
        if sub.dependents is not None:
            items_to_save["dependents"] = str(sub.dependents)
        if sub.monthly_salary is not None:
            items_to_save["monthly_salary"] = str(sub.monthly_salary)
        if sub.other_monthly_income is not None:
            items_to_save["other_monthly_income"] = str(sub.other_monthly_income)
        if sub.income_stability is not None:
            items_to_save["income_stability"] = str(sub.income_stability)
        if sub.monthly_expenses is not None:
            items_to_save["monthly_expenses"] = str(sub.monthly_expenses)
        if sub.discretionary_expenses is not None:
            items_to_save["discretionary_expenses"] = str(sub.discretionary_expenses)
        if sub.monthly_emi is not None:
            items_to_save["monthly_emi"] = str(sub.monthly_emi)
        if sub.debt_types is not None:
            if isinstance(sub.debt_types, list):
                items_to_save["debt_types"] = ", ".join(sub.debt_types)
            else:
                items_to_save["debt_types"] = str(sub.debt_types)
        if sub.emergency_fund is not None:
            items_to_save["emergency_fund"] = str(sub.emergency_fund)
        if sub.target_emergency_months is not None:
            items_to_save["target_emergency_months"] = str(sub.target_emergency_months)
        if sub.insurance_health is not None:
            items_to_save["insurance_health"] = str(sub.insurance_health)
        if sub.insurance_term is not None:
            items_to_save["insurance_term"] = str(sub.insurance_term)
        if sub.existing_investment_amount is not None:
            items_to_save["existing_investment_amount"] = str(sub.existing_investment_amount)
        if sub.investment_experience is not None:
            items_to_save["investment_experience"] = str(sub.investment_experience)
        if sub.risk_tolerance is not None:
            items_to_save["risk_tolerance"] = str(sub.risk_tolerance)
        if sub.market_drop_reaction is not None:
            items_to_save["market_drop_reaction"] = str(sub.market_drop_reaction)
        if sub.primary_goal is not None:
            items_to_save["primary_goal"] = str(sub.primary_goal)
        if sub.investment_horizon is not None:
            items_to_save["investment_horizon"] = str(sub.investment_horizon)
        if sub.target_monthly_sip is not None:
            items_to_save["target_monthly_sip"] = str(sub.target_monthly_sip)
        if sub.existing_investments is not None:
            if isinstance(sub.existing_investments, list):
                items_to_save["existing_investments"] = ", ".join(sub.existing_investments)
            else:
                items_to_save["existing_investments"] = str(sub.existing_investments)
        if sub.tax_regime is not None:
            items_to_save["tax_regime"] = str(sub.tax_regime)
        if sub.section_80c_status is not None:
            items_to_save["section_80c_status"] = str(sub.section_80c_status)
        if sub.financial_preferences is not None:
            items_to_save["financial_preferences"] = str(sub.financial_preferences)

        if sub.raw_responses:
            for r in sub.raw_responses:
                items_to_save[r.question_key] = r.answer

        for k, v in items_to_save.items():
            existing = db.query(UserQuestionnaire).filter(
                UserQuestionnaire.user_id == user_id,
                UserQuestionnaire.question_key == k
            ).first()
            if existing:
                existing.answer = v
            else:
                db.add(UserQuestionnaire(user_id=user_id, question_key=k, answer=v))

        # 2. Parse investment horizon into integer years
        horizon_years = 5
        if sub.investment_horizon:
            h_str = sub.investment_horizon.lower()
            if "1-3" in h_str or "1–3" in h_str or "short" in h_str:
                horizon_years = 3
            elif "3-5" in h_str or "3–5" in h_str or "medium" in h_str:
                horizon_years = 5
            elif "5-10" in h_str or "5–10" in h_str or "long" in h_str:
                horizon_years = 10
            elif "10+" in h_str or "10" in h_str:
                horizon_years = 15

        # 3. Update or synthesize FinancialProfile
        profile = ProfileService.get_or_create_profile(db, user_id)
        if sub.age is not None:
            profile.age = sub.age
        if sub.employment_type is not None:
            profile.employment_type = sub.employment_type
        if sub.city_tier is not None:
            profile.city_tier = sub.city_tier
        if sub.dependents is not None:
            profile.dependents = sub.dependents
        if sub.monthly_salary is not None:
            profile.monthly_salary = sub.monthly_salary
        if sub.other_monthly_income is not None:
            profile.other_monthly_income = sub.other_monthly_income
        if sub.monthly_expenses is not None:
            # If discretionary is passed separately, include it in total expenses
            disc = float(sub.discretionary_expenses or 0.0)
            profile.monthly_expenses = float(sub.monthly_expenses) + disc
        if sub.monthly_emi is not None:
            profile.monthly_emi = sub.monthly_emi
        if sub.emergency_fund is not None:
            profile.emergency_fund_balance = sub.emergency_fund
            profile.bank_balance = sub.emergency_fund
        if sub.target_emergency_months is not None:
            profile.target_emergency_months = sub.target_emergency_months
        if sub.existing_investment_amount is not None:
            profile.existing_investments = sub.existing_investment_amount
        if sub.risk_tolerance is not None:
            profile.risk_tolerance = sub.risk_tolerance
        profile.investment_horizon_years = horizon_years

        # 4. If primary goal is supplied, create or update FinancialGoal
        if sub.primary_goal:
            goal = db.query(FinancialGoal).filter(FinancialGoal.profile_id == profile.id).first()
            target_amount = 1000000.0
            if sub.target_monthly_sip and sub.target_monthly_sip > 0:
                # Estimate future value with modest 12% compounding over horizon
                months = horizon_years * 12
                r = 0.12 / 12
                target_amount = round(sub.target_monthly_sip * (((1 + r) ** months - 1) / r) * (1 + r), 2)

            if not goal:
                goal = FinancialGoal(
                    profile_id=profile.id,
                    name=sub.primary_goal,
                    target_amount=target_amount,
                    current_amount=float(profile.existing_investments or 0.0),
                    target_year=datetime.utcnow().year + horizon_years,
                    expected_return_pct=12.0,
                    priority="High"
                )
                db.add(goal)
            else:
                goal.name = sub.primary_goal
                goal.target_amount = target_amount
                goal.target_year = datetime.utcnow().year + horizon_years

        db.commit()
        db.refresh(profile)

        # 5. Create Historical Baseline Snapshot for Instant Dashboard Analytics
        try:
            total_assets = float(profile.bank_balance or 0.0) + float(profile.existing_investments or 0.0)
            total_liabilities = float(profile.monthly_emi or 0.0) * 12.0

            snapshot = FinancialProfileSnapshot(
                user_id=user_id,
                monthly_income=float(profile.monthly_salary or 0.0) + float(profile.other_monthly_income or 0.0),
                monthly_expenses=float(profile.monthly_expenses or 0.0),
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                profile_data_json={
                    "age": profile.age,
                    "employment_type": profile.employment_type,
                    "city_tier": profile.city_tier,
                    "dependents": profile.dependents,
                    "monthly_salary": float(profile.monthly_salary or 0),
                    "other_monthly_income": float(profile.other_monthly_income or 0),
                    "monthly_expenses": float(profile.monthly_expenses or 0),
                    "monthly_emi": float(profile.monthly_emi or 0),
                    "risk_tolerance": profile.risk_tolerance,
                    "primary_goal": sub.primary_goal,
                    "investment_horizon": sub.investment_horizon,
                    "target_monthly_sip": sub.target_monthly_sip,
                    "tax_regime": sub.tax_regime,
                }
            )
            db.add(snapshot)
            db.commit()
        except Exception:
            db.rollback()

        return profile

    @staticmethod
    def get_questionnaire(db: Session, user_id: str) -> List[UserQuestionnaire]:
        return db.query(UserQuestionnaire).filter(UserQuestionnaire.user_id == user_id).all()

