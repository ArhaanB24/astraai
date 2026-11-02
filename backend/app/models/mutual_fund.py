import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class MutualFund(Base):
    __tablename__ = "mutual_funds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)  # AMFI Code
    scheme_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    isin: Mapped[str] = mapped_column(String(50), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)  # Flexi Cap, Large Cap, Small Cap, etc.
    sub_category: Mapped[str] = mapped_column(String(100), nullable=True)
    fund_house: Mapped[str] = mapped_column(String(150), nullable=True)  # AMC Name
    current_nav: Mapped[float] = mapped_column(Float, nullable=True)
    nav_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=True)  # Very High, High, Moderate, etc.
    expense_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    aum_crores: Mapped[float] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    nav_history = relationship("FundNAVHistory", back_populates="fund", cascade="all, delete-orphan")
    holdings = relationship("FundHolding", back_populates="fund", cascade="all, delete-orphan")
    transactions = relationship("FundTransaction", back_populates="fund")


class FundNAVHistory(Base):
    __tablename__ = "fund_nav_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_id: Mapped[str] = mapped_column(String(36), ForeignKey("mutual_funds.id"), nullable=False)
    nav_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    nav: Mapped[float] = mapped_column(Float, nullable=False)

    fund = relationship("MutualFund", back_populates="nav_history")


class FundHolding(Base):
    __tablename__ = "fund_holdings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fund_id: Mapped[str] = mapped_column(String(36), ForeignKey("mutual_funds.id"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=True)
    allocation_percentage: Mapped[float] = mapped_column(Float, nullable=False)  # e.g., 8.5 for 8.5%
    as_of_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    fund = relationship("MutualFund", back_populates="holdings")
