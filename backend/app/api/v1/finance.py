from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.personal_finance import (
    IncomeSourceCreate,
    ExpenseItemCreate,
    AssetItemCreate,
    LiabilityItemCreate,
    FinancialGoalCreate,
    CarAffordabilityRequest,
    ScenarioSimulationRequest
)
from app.services.personal_finance_service import PersonalFinanceService

router = APIRouter(prefix="/finance", tags=["Personal Finance AI"])
finance_service = PersonalFinanceService()


@router.get("/summary")
def get_finance_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return finance_service.build_profile_dict(db, current_user.id)


@router.get("/health")
def get_financial_health(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return finance_service.get_financial_health_summary(db, current_user.id)


@router.post("/income")
def add_income_source(item: IncomeSourceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return finance_service.add_income_source(db, current_user.id, item)


@router.post("/expenses")
def add_expense_item(item: ExpenseItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return finance_service.add_expense_item(db, current_user.id, item)


@router.post("/assets")
def add_asset_item(item: AssetItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return finance_service.add_asset_item(db, current_user.id, item)


@router.post("/liabilities")
def add_liability_item(item: LiabilityItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return finance_service.add_liability_item(db, current_user.id, item)


@router.post("/goals")
def add_financial_goal(item: FinancialGoalCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return finance_service.add_financial_goal(db, current_user.id, item)


@router.post("/affordability")
def calculate_affordability(req: CarAffordabilityRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return finance_service.calculate_car_affordability(db, current_user.id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scenarios")
@router.post("/scenarios/simulate")
def simulate_scenario(req: ScenarioSimulationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return finance_service.simulate_scenario(db, current_user.id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/profile")
def update_financial_profile(
    profile_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = finance_service.get_or_create_profile(db, current_user.id)
    for field in [
        "monthly_salary", "other_monthly_income", "monthly_expenses", "monthly_emi",
        "bank_balance", "existing_investments", "emergency_fund_balance", "target_emergency_months",
        "risk_tolerance", "investment_horizon_years", "age", "city_tier"
    ]:
        if field in profile_data:
            setattr(profile, field, profile_data[field])
    db.commit()
    db.refresh(profile)
    return finance_service.build_profile_dict(db, current_user.id)


@router.delete("/income/{item_id}")
def delete_income_source(item_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.profile import IncomeSource
    profile = finance_service.get_or_create_profile(db, current_user.id)
    item = db.query(IncomeSource).filter(IncomeSource.id == item_id, IncomeSource.profile_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Income source not found")
    db.delete(item)
    db.commit()
    return {"message": "Income source deleted"}


@router.delete("/expenses/{item_id}")
def delete_expense_item(item_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.profile import ExpenseItem
    profile = finance_service.get_or_create_profile(db, current_user.id)
    item = db.query(ExpenseItem).filter(ExpenseItem.id == item_id, ExpenseItem.profile_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Expense item not found")
    db.delete(item)
    db.commit()
    return {"message": "Expense item deleted"}


@router.delete("/assets/{item_id}")
def delete_asset_item(item_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.profile import AssetItem
    profile = finance_service.get_or_create_profile(db, current_user.id)
    item = db.query(AssetItem).filter(AssetItem.id == item_id, AssetItem.profile_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Asset item not found")
    db.delete(item)
    db.commit()
    return {"message": "Asset item deleted"}


@router.delete("/liabilities/{item_id}")
def delete_liability_item(item_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.profile import LiabilityItem
    profile = finance_service.get_or_create_profile(db, current_user.id)
    item = db.query(LiabilityItem).filter(LiabilityItem.id == item_id, LiabilityItem.profile_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Liability item not found")
    db.delete(item)
    db.commit()
    return {"message": "Liability item deleted"}


@router.delete("/goals/{goal_id}")
def delete_financial_goal(goal_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.profile import FinancialGoal
    profile = finance_service.get_or_create_profile(db, current_user.id)
    item = db.query(FinancialGoal).filter(FinancialGoal.id == goal_id, FinancialGoal.profile_id == profile.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(item)
    db.commit()
    return {"message": "Goal deleted"}


@router.post("/chat")
def finance_chat(payload: Dict[str, Any], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = payload.get("message", "What is my financial health?")
    session_id = payload.get("session_id")
    if not session_id:
        session = db.query(ChatSession).filter(ChatSession.user_id == current_user.id, ChatSession.title == "Personal Finance Advisory").order_by(ChatSession.created_at.desc()).first()
        if not session:
            session = ChatSession(user_id=current_user.id, title="Personal Finance Advisory")
            db.add(session)
            db.commit()
            db.refresh(session)
        session_id = session.id

    user_msg = ChatMessage(session_id=session_id, sender="user", content=query)
    db.add(user_msg)
    db.commit()

    prev_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(20).all()
    history = [{"role": m.sender, "content": m.content} for m in reversed(prev_messages)]

    agent_res = finance_service.process_chat_query(db, current_user.id, query, conversation_history=history)

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
