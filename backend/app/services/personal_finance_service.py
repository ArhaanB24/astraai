from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.profile import (
    FinancialProfile,
    IncomeSource,
    ExpenseItem,
    AssetItem,
    LiabilityItem,
    FinancialGoal,
    FinancialProfileSnapshot
)
from app.schemas.personal_finance import (
    IncomeSourceCreate,
    ExpenseItemCreate,
    AssetItemCreate,
    LiabilityItemCreate,
    FinancialGoalCreate,
    CarAffordabilityRequest,
    ScenarioSimulationRequest
)
from app.engines.personal_finance import calculate_financial_health, calculate_goal_required_sip
from app.engines.affordability import calculate_purchase_affordability
from app.engines.scenario_simulator import simulate_what_if_scenario
from app.agents.personal_finance_agent import PersonalFinanceAgent


class PersonalFinanceService:

    def __init__(self):
        self.agent = PersonalFinanceAgent()

    def get_or_create_profile(self, db: Session, user_id: str) -> FinancialProfile:
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
        if not profile:
            profile = FinancialProfile(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    def build_profile_dict(self, db: Session, user_id: str) -> Dict[str, Any]:
        profile = self.get_or_create_profile(db, user_id)
        incomes = db.query(IncomeSource).filter(IncomeSource.profile_id == profile.id).all()
        expenses = db.query(ExpenseItem).filter(ExpenseItem.profile_id == profile.id).all()
        assets = db.query(AssetItem).filter(AssetItem.profile_id == profile.id).all()
        liabilities = db.query(LiabilityItem).filter(LiabilityItem.profile_id == profile.id).all()
        goals = db.query(FinancialGoal).filter(FinancialGoal.profile_id == profile.id).all()

        goals_list = []
        for g in goals:
            pmt = calculate_goal_required_sip(
                target_amount=g.target_amount,
                current_amount=g.current_amount,
                target_year=g.target_year,
                expected_return_pct=g.expected_return_pct
            )
            goals_list.append({
                "id": g.id,
                "name": g.name,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "target_year": g.target_year,
                "expected_return_pct": g.expected_return_pct,
                "priority": g.priority,
                "required_monthly_contribution": pmt["required_monthly_contribution"]
            })

        return {
            "profile_id": profile.id,
            "user_id": user_id,
            "monthly_salary": profile.monthly_salary,
            "other_monthly_income": profile.other_monthly_income,
            "monthly_expenses": profile.monthly_expenses,
            "monthly_emi": profile.monthly_emi,
            "bank_balance": profile.bank_balance,
            "existing_investments": profile.existing_investments,
            "emergency_fund_balance": profile.emergency_fund_balance,
            "target_emergency_months": profile.target_emergency_months,
            "risk_tolerance": profile.risk_tolerance,
            "income_sources": [{"id": i.id, "name": i.name, "category": i.category, "amount": i.amount, "frequency": i.frequency} for i in incomes],
            "expense_items": [{"id": e.id, "name": e.name, "category": e.category, "amount": e.amount, "is_essential": e.is_essential} for e in expenses],
            "asset_items": [{"id": a.id, "name": a.name, "category": a.category, "amount": a.amount, "liquidity_tier": a.liquidity_tier} for a in assets],
            "liability_items": [{"id": l.id, "name": l.name, "category": l.category, "principal_outstanding": l.principal_outstanding, "monthly_emi": l.monthly_emi, "interest_rate_pct": l.interest_rate_pct, "tenure_months_left": l.tenure_months_left} for l in liabilities],
            "goals": goals_list
        }

    def get_financial_health_summary(self, db: Session, user_id: str) -> Dict[str, Any]:
        p_dict = self.build_profile_dict(db, user_id)
        health = calculate_financial_health(p_dict)
        return {**health, "profile": p_dict}

    def add_income_source(self, db: Session, user_id: str, item_in: IncomeSourceCreate) -> IncomeSource:
        profile = self.get_or_create_profile(db, user_id)
        item = IncomeSource(
            profile_id=profile.id,
            name=item_in.name,
            category=item_in.category,
            amount=item_in.amount,
            frequency=item_in.frequency
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def add_expense_item(self, db: Session, user_id: str, item_in: ExpenseItemCreate) -> ExpenseItem:
        profile = self.get_or_create_profile(db, user_id)
        item = ExpenseItem(
            profile_id=profile.id,
            name=item_in.name,
            category=item_in.category,
            amount=item_in.amount,
            is_essential=item_in.is_essential
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def add_asset_item(self, db: Session, user_id: str, item_in: AssetItemCreate) -> AssetItem:
        profile = self.get_or_create_profile(db, user_id)
        item = AssetItem(
            profile_id=profile.id,
            name=item_in.name,
            category=item_in.category,
            amount=item_in.amount,
            liquidity_tier=item_in.liquidity_tier
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def add_liability_item(self, db: Session, user_id: str, item_in: LiabilityItemCreate) -> LiabilityItem:
        profile = self.get_or_create_profile(db, user_id)
        item = LiabilityItem(
            profile_id=profile.id,
            name=item_in.name,
            category=item_in.category,
            principal_outstanding=item_in.principal_outstanding,
            monthly_emi=item_in.monthly_emi,
            interest_rate_pct=item_in.interest_rate_pct,
            tenure_months_left=item_in.tenure_months_left
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def add_financial_goal(self, db: Session, user_id: str, item_in: FinancialGoalCreate) -> FinancialGoal:
        profile = self.get_or_create_profile(db, user_id)
        item = FinancialGoal(
            profile_id=profile.id,
            name=item_in.name,
            target_amount=item_in.target_amount,
            current_amount=item_in.current_amount,
            target_year=item_in.target_year,
            expected_return_pct=item_in.expected_return_pct,
            priority=item_in.priority
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def calculate_car_affordability(self, db: Session, user_id: str, req: CarAffordabilityRequest) -> Dict[str, Any]:
        p_dict = self.build_profile_dict(db, user_id)
        health = calculate_financial_health(p_dict)

        aff_result = calculate_purchase_affordability(
            purchase_price=req.car_price,
            down_payment=req.down_payment,
            loan_interest_rate_pct=req.interest_rate_pct,
            loan_tenure_years=req.tenure_years,
            monthly_income=health["monthly_income"],
            monthly_expenses=health["monthly_expenses"],
            existing_emis=health["monthly_emis"],
            emergency_fund_balance=health["emergency_fund_balance"],
            monthly_sip=float(p_dict.get("monthly_sip", 0.0)),
            goals=p_dict.get("goals", [])
        )
        return {**aff_result, "financial_health": health}

    def simulate_scenario(self, db: Session, user_id: str, req: ScenarioSimulationRequest) -> Dict[str, Any]:
        p_dict = self.build_profile_dict(db, user_id)
        return simulate_what_if_scenario(
            baseline_profile=p_dict,
            scenario_type=req.scenario_type,
            scenario_params=req.scenario_params
        )

    def process_chat_query(self, db: Session, user_id: str, query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        p_dict = self.build_profile_dict(db, user_id)
        return self.agent.process_query(db, user_id, p_dict, query, conversation_history=conversation_history)
