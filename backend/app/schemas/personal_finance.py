from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class IncomeSourceCreate(BaseModel):
    name: str = Field(..., example="Primary Salary")
    category: str = Field("Salary", example="Salary")
    amount: float = Field(..., gt=0)
    frequency: str = Field("Monthly", example="Monthly")


class IncomeSourceResponse(IncomeSourceCreate):
    id: str
    profile_id: str

    class Config:
        from_attributes = True


class ExpenseItemCreate(BaseModel):
    name: str = Field(..., example="Rent")
    category: str = Field("Essential", example="Essential")
    amount: float = Field(..., gt=0)
    is_essential: bool = True


class ExpenseItemResponse(ExpenseItemCreate):
    id: str
    profile_id: str

    class Config:
        from_attributes = True


class AssetItemCreate(BaseModel):
    name: str = Field(..., example="Mutual Funds")
    category: str = Field("Equity", example="Equity")
    amount: float = Field(..., gt=0)
    liquidity_tier: str = Field("High", example="High")


class AssetItemResponse(AssetItemCreate):
    id: str
    profile_id: str

    class Config:
        from_attributes = True


class LiabilityItemCreate(BaseModel):
    name: str = Field(..., example="Home Loan")
    category: str = Field("Loan", example="Loan")
    principal_outstanding: float = Field(..., gt=0)
    monthly_emi: float = Field(..., gt=0)
    interest_rate_pct: float = 8.5
    tenure_months_left: int = 60


class LiabilityItemResponse(LiabilityItemCreate):
    id: str
    profile_id: str

    class Config:
        from_attributes = True


class FinancialGoalCreate(BaseModel):
    name: str = Field(..., example="Car Purchase")
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(0.0, ge=0)
    target_year: int = Field(..., example=2028)
    expected_return_pct: float = 10.0
    priority: str = Field("High", example="High")


class FinancialGoalResponse(FinancialGoalCreate):
    id: str
    profile_id: str
    required_monthly_contribution: float = 0.0

    class Config:
        from_attributes = True


class CarAffordabilityRequest(BaseModel):
    car_price: float = Field(1500000.0, example=1500000.0)
    down_payment: float = Field(300000.0, example=300000.0)
    interest_rate_pct: float = Field(8.5, example=8.5)
    tenure_years: float = Field(5.0, example=5.0)


class ScenarioSimulationRequest(BaseModel):
    scenario_type: str = Field(..., example="BUY_CAR")  # BUY_CAR, SALARY_CHANGE, EXPENSE_INCREASE, INCREASE_SIP, INCOME_LOSS
    scenario_params: Dict[str, Any] = Field(default_factory=dict)
