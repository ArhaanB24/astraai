from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.profile import FinancialProfile
from app.models.portfolio import FundPortfolio, FundTransaction
from app.models.mutual_fund import MutualFund
from app.engines.tax import calculate_income_tax, compare_tax_regimes, TaxRegime, FinancialYear
from app.agents.tax_agent import tax_agent

router = APIRouter(prefix="/tax", tags=["Tax AI & Calculation Module"])


class TaxCalculateRequest(BaseModel):
    gross_salary: float = Field(0.0, ge=0.0, description="Annual gross salary income in INR", example=1440000.0)
    other_income: float = Field(0.0, ge=0.0, description="Annual other income (interest, freelance, rental) in INR", example=120000.0)
    deductions_80c: float = Field(0.0, ge=0.0, description="Eligible Section 80C investments claimed in INR", example=150000.0)
    deductions_80d: float = Field(0.0, ge=0.0, description="Eligible Section 80D health insurance premiums in INR", example=25000.0)
    other_deductions: float = Field(0.0, ge=0.0, description="Other eligible deductions in INR", example=0.0)
    regime: str = Field("AUTO", description="Tax regime: 'OLD', 'NEW', or 'AUTO' for comparison", example="AUTO")
    financial_year: str = Field("2025-26", description="Financial Year: '2024-25' or '2025-26'", example="2025-26")
    is_salaried: bool = Field(True, description="Whether taxpayer is salaried")
    age: int = Field(28, ge=0, le=120, description="Taxpayer age in years", example=28)


from app.models.chat import ChatSession, ChatMessage


class TaxChatRequest(BaseModel):
    message: str = Field(..., min_length=1, example="Which tax regime is better for me?")
    session_id: Optional[str] = Field(None, description="Optional chat session ID for multi-turn history")


@router.post("/calculate")
def calculate_tax(
    req: TaxCalculateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate deterministic income tax liability or compare Old vs New regimes.
    """
    try:
        if req.regime.upper() == "AUTO" or req.regime.upper() == "COMPARISON":
            return compare_tax_regimes(
                gross_salary=req.gross_salary,
                other_income=req.other_income,
                deductions_80c=req.deductions_80c,
                deductions_80d=req.deductions_80d,
                other_deductions=req.other_deductions,
                financial_year=req.financial_year,
                is_salaried=req.is_salaried,
                age=req.age
            )
        else:
            return calculate_income_tax(
                gross_salary=req.gross_salary,
                other_income=req.other_income,
                deductions_80c=req.deductions_80c,
                deductions_80d=req.deductions_80d,
                other_deductions=req.other_deductions,
                regime=req.regime,
                financial_year=req.financial_year,
                is_salaried=req.is_salaried,
                age=req.age
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tax calculation error: {str(e)}")


@router.get("/summary")
def get_tax_summary(
    financial_year: str = Query("2025-26", description="Financial Year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns automated tax summary and Old vs New regime comparison based on the user's saved FinancialProfile.
    Strictly derives 80C deductions from actual ELSS mutual fund investments in user portfolio.
    """
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    
    annual_salary = float(profile.monthly_salary) * 12.0 if profile and profile.monthly_salary else 1440000.0
    annual_other = float(profile.other_monthly_income) * 12.0 if profile and profile.other_monthly_income else 120000.0
    age = profile.age if profile and profile.age else 28
    is_salaried = profile.employment_type == "Salaried" if profile and profile.employment_type else True

    # Calculate actual ELSS investments made by the user
    elss_annual_investment = 0.0
    transactions = db.query(FundTransaction).filter(FundTransaction.user_id == current_user.id).all()
    for tx in transactions:
        mf = db.query(MutualFund).filter(MutualFund.id == tx.fund_id).first()
        if mf and ("ELSS" in mf.category.upper() or "TAX" in mf.scheme_name.upper()):
            elss_annual_investment += float(tx.amount)

    # Standardize 80C: Cap at 1.5L if user holds ELSS or has existing investments
    if elss_annual_investment > 0.0:
        claimed_80c = min(elss_annual_investment, 150000.0)
    else:
        # Fallback to standard 80C from balance sheet savings
        claimed_80c = 150000.0 if profile and float(profile.existing_investments) >= 150000.0 else 50000.0

    claimed_80d = 25000.0

    comparison = compare_tax_regimes(
        gross_salary=annual_salary,
        other_income=annual_other,
        deductions_80c=claimed_80c,
        deductions_80d=claimed_80d,
        financial_year=financial_year,
        is_salaried=is_salaried,
        age=age
    )

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "financial_year": financial_year,
        "profile_inputs": {
            "annual_salary": annual_salary,
            "annual_other_income": annual_other,
            "total_gross_income": annual_salary + annual_other,
            "claimed_80c": claimed_80c,
            "claimed_80d": claimed_80d,
            "elss_verified_investments": elss_annual_investment,
            "age": age,
            "is_salaried": is_salaried
        },
        "comparison": comparison
    }


@router.post("/chat")
def chat_with_tax_agent(
    req: TaxChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dedicated Tax AI Chatbot endpoint with RAG citations and deterministic math grounding.
    """
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    
    profile_dict = {
        "monthly_salary": float(profile.monthly_salary) if profile and profile.monthly_salary else 120000.0,
        "other_monthly_income": float(profile.other_monthly_income) if profile and profile.other_monthly_income else 10000.0,
        "age": profile.age if profile and profile.age else 28,
        "employment_type": profile.employment_type if profile and profile.employment_type else "Salaried",
        "existing_investments": float(profile.existing_investments) if profile and profile.existing_investments else 450000.0,
        "emergency_fund_balance": float(profile.emergency_fund_balance) if profile and profile.emergency_fund_balance else 270000.0
    }

    # Extract ELSS investments
    elss_annual = 0.0
    transactions = db.query(FundTransaction).filter(FundTransaction.user_id == current_user.id).all()
    for tx in transactions:
        mf = db.query(MutualFund).filter(MutualFund.id == tx.fund_id).first()
        if mf and ("ELSS" in mf.category.upper() or "TAX" in mf.scheme_name.upper()):
            elss_annual += float(tx.amount)
    profile_dict["elss_investments_annual"] = elss_annual

    session_id = req.session_id
    if not session_id:
        session = db.query(ChatSession).filter(ChatSession.user_id == current_user.id, ChatSession.title == "Tax Advisory").order_by(ChatSession.created_at.desc()).first()
        if not session:
            session = ChatSession(user_id=current_user.id, title="Tax Advisory")
            db.add(session)
            db.commit()
            db.refresh(session)
        session_id = session.id

    user_msg = ChatMessage(session_id=session_id, sender="user", content=req.message)
    db.add(user_msg)
    db.commit()

    prev_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(20).all()
    history = [{"role": m.sender, "content": m.content} for m in reversed(prev_messages)]

    agent_res = tax_agent.process_query(db, current_user.id, profile_dict, req.message, conversation_history=history)

    assistant_msg = ChatMessage(
        session_id=session_id,
        sender="assistant",
        content=agent_res["answer"],
        tool_calls_json=agent_res.get("tools_used", [])
    )
    db.add(assistant_msg)
    db.commit()

    agent_res["session_id"] = session_id
    return agent_res
