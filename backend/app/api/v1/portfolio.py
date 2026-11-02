from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.schemas.portfolio import (
    TransactionCreate,
    TransactionResponse,
    PortfolioSummaryResponse,
    StockHoldingCreate,
    StockHoldingResponse
)
from app.services.portfolio_service import PortfolioService
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/portfolio", tags=["Mutual Fund Portfolio"])
portfolio_service = PortfolioService()


@router.get("", response_model=PortfolioSummaryResponse)
def get_portfolio_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return portfolio_service.get_portfolio_summary(db, current_user.id)


@router.get("/history")
def get_portfolio_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return portfolio_service.get_portfolio_history_series(db, current_user.id)


@router.post("/transactions", response_model=TransactionResponse)
def add_transaction(
    tx_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return portfolio_service.add_transaction(db, current_user.id, tx_in)


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = portfolio_service.delete_transaction(db, current_user.id, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}


@router.get("/overlap")
def get_portfolio_overlap(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return portfolio_service.get_portfolio_overlap_analysis(db, current_user.id)


@router.get("/stocks", response_model=List[StockHoldingResponse])
def get_stock_holdings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return portfolio_service.get_stock_holdings(db, current_user.id)


@router.post("/stocks", response_model=StockHoldingResponse)
def add_stock_holding(
    stock_in: StockHoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return portfolio_service.add_stock_holding(db, current_user.id, stock_in)


@router.delete("/stocks/{stock_id}")
def delete_stock_holding(
    stock_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = portfolio_service.delete_stock_holding(db, current_user.id, stock_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stock holding not found")
    return {"message": "Stock holding deleted successfully"}


@router.get("/risk")
def get_portfolio_risk(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return portfolio_service.get_portfolio_risk_analysis(db, current_user.id)
