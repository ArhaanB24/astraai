from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class TransactionCreate(BaseModel):
    scheme_code: str
    scheme_name: str
    transaction_type: str = "SIP"  # SIP, BUY, SELL, DIVIDEND
    transaction_date: str  # YYYY-MM-DD
    units: float
    nav: float
    amount: float


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    portfolio_id: str
    fund_id: str
    scheme_code: str
    scheme_name: str
    transaction_type: str
    transaction_date: datetime
    units: float
    nav: float
    amount: float

    class Config:
        from_attributes = True


class PortfolioSummaryResponse(BaseModel):
    total_invested: float
    current_value: float
    total_profit_loss: float
    profit_loss_percentage: float
    xirr: Optional[float] = None
    fund_breakdown: List[Dict[str, Any]]
    direct_stocks: Optional[List[Dict[str, Any]]] = None


class StockHoldingCreate(BaseModel):
    symbol: str
    company_name: str
    sector: Optional[str] = "General"
    quantity: float = 1.0
    buy_price: float
    current_price: Optional[float] = None


class StockHoldingResponse(BaseModel):
    id: str
    user_id: str
    portfolio_id: str
    symbol: str
    company_name: str
    sector: str
    quantity: float
    buy_price: float
    current_price: Optional[float] = None
    invested_value: float
    current_value: float
    profit_loss: float
    profit_loss_pct: float

    class Config:
        from_attributes = True
