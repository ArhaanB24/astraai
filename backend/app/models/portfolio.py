import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum
import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TransactionType(str, enum.Enum):
    SIP = "SIP"
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"


class FundPortfolio(Base):
    __tablename__ = "fund_portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="Primary Portfolio")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="portfolios")
    transactions = relationship("FundTransaction", back_populates="portfolio", cascade="all, delete-orphan")
    stocks = relationship("StockHolding", back_populates="portfolio", cascade="all, delete-orphan")


class FundTransaction(Base):
    __tablename__ = "fund_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("fund_portfolios.id"), nullable=False)
    fund_id: Mapped[str] = mapped_column(String(36), ForeignKey("mutual_funds.id"), nullable=False)

    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # BUY, SELL, SIP, DIVIDEND
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    units: Mapped[float] = mapped_column(Float, nullable=False)
    nav: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    portfolio = relationship("FundPortfolio", back_populates="transactions")
    fund = relationship("MutualFund", back_populates="transactions")


class StockHolding(Base):
    __tablename__ = "stock_holdings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("fund_portfolios.id"), nullable=False)

    symbol: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., TATAPOWER, SUZLON, RELIANCE
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)  # e.g., Tata Power Co. Ltd.
    sector: Mapped[str] = mapped_column(String(100), default="General")  # e.g., Energy, Financial Services
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    buy_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolio = relationship("FundPortfolio", back_populates="stocks")
