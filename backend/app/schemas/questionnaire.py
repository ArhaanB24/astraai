from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union


class QuestionnaireAnswer(BaseModel):
    question_key: str
    answer: str
    answer_metadata: Optional[Dict[str, Any]] = None


class QuestionnaireSubmission(BaseModel):
    # Core demographic & identity
    full_name: Optional[str] = None
    age: Optional[int] = None
    employment_type: Optional[str] = None
    city_tier: Optional[str] = None
    dependents: Optional[int] = None

    # Income & cash flow
    monthly_salary: Optional[float] = None
    other_monthly_income: Optional[float] = None
    income_stability: Optional[str] = None

    # Living expenses, lifestyle & debt
    monthly_expenses: Optional[float] = None
    discretionary_expenses: Optional[float] = None
    monthly_emi: Optional[float] = None
    debt_types: Optional[Union[str, List[str]]] = None

    # Emergency fund & insurance protection
    emergency_fund: Optional[float] = None
    target_emergency_months: Optional[int] = None
    insurance_health: Optional[str] = None
    insurance_term: Optional[str] = None

    # Existing wealth & investments
    existing_investments: Optional[Union[str, List[str]]] = None
    existing_investment_amount: Optional[float] = None

    # Psychological risk & behavioral tolerance
    investment_experience: Optional[str] = None
    risk_tolerance: Optional[str] = None
    market_drop_reaction: Optional[str] = None

    # Financial goals & horizon
    primary_goal: Optional[str] = None
    investment_horizon: Optional[str] = None
    target_monthly_sip: Optional[float] = None

    # Tax planning & strategy preferences
    tax_regime: Optional[str] = None
    section_80c_status: Optional[str] = None
    financial_preferences: Optional[str] = None

    raw_responses: Optional[List[QuestionnaireAnswer]] = None


class QuestionnaireResponse(BaseModel):
    id: str
    user_id: str
    question_key: str
    answer: str
    answer_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
