from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class FinancialProfileCreate(BaseModel):
    age: Optional[int] = 25
    employment_type: Optional[str] = "Salaried"
    dependents: Optional[int] = 0
    city_tier: Optional[str] = "Tier 1"
    monthly_salary: Optional[float] = 100000.0
    other_monthly_income: Optional[float] = 0.0
    monthly_expenses: Optional[float] = 40000.0
    monthly_emi: Optional[float] = 10000.0
    bank_balance: Optional[float] = 150000.0
    existing_investments: Optional[float] = 200000.0
    risk_tolerance: Optional[str] = "Moderate"
    investment_horizon_years: Optional[int] = 5
    goals_json: Optional[List[Dict[str, Any]]] = []


class FinancialProfileResponse(FinancialProfileCreate):
    id: str
    user_id: str

    class Config:
        from_attributes = True
