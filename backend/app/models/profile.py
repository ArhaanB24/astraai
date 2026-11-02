import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class FinancialProfile(Base):
    """
    Shared Financial Profile Model.
    Single source of truth for user financial state across Personal Finance AI, Tax AI, and Mutual Fund AI.
    All monetary fields use SQL Numeric(18, 2) to eliminate binary floating point inaccuracies.
    """
    __tablename__ = "financial_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Basic Info
    age: Mapped[int] = mapped_column(Integer, nullable=True, default=28)
    employment_type: Mapped[str] = mapped_column(String(100), nullable=True, default="Salaried")
    dependents: Mapped[int] = mapped_column(Integer, default=1)
    city_tier: Mapped[str] = mapped_column(String(50), nullable=True, default="Tier 1")

    # Income & Expense Breakdown (Monthly)
    monthly_salary: Mapped[float] = mapped_column(Numeric(18, 2), default=120000.00)
    other_monthly_income: Mapped[float] = mapped_column(Numeric(18, 2), default=0.00)
    monthly_expenses: Mapped[float] = mapped_column(Numeric(18, 2), default=45000.00)
    monthly_emi: Mapped[float] = mapped_column(Numeric(18, 2), default=15000.00)

    # Asset & Liquidity Summary
    bank_balance: Mapped[float] = mapped_column(Numeric(18, 2), default=250000.00)
    existing_investments: Mapped[float] = mapped_column(Numeric(18, 2), default=450000.00)
    emergency_fund_balance: Mapped[float] = mapped_column(Numeric(18, 2), default=270000.00)
    target_emergency_months: Mapped[int] = mapped_column(Integer, default=6)

    # Risk Profile
    risk_tolerance: Mapped[str] = mapped_column(String(50), default="Moderate")
    investment_horizon_years: Mapped[int] = mapped_column(Integer, default=5)

    # Legacy Goals JSON (preserved for backward compatibility)
    goals_json: Mapped[dict] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="financial_profile")
    income_sources = relationship("IncomeSource", back_populates="profile", cascade="all, delete-orphan")
    expense_items = relationship("ExpenseItem", back_populates="profile", cascade="all, delete-orphan")
    asset_items = relationship("AssetItem", back_populates="profile", cascade="all, delete-orphan")
    liability_items = relationship("LiabilityItem", back_populates="profile", cascade="all, delete-orphan")
    goals = relationship("FinancialGoal", back_populates="profile", cascade="all, delete-orphan")


class IncomeSource(Base):
    __tablename__ = "income_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., Primary Salary, Rental Income
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Salary")  # Salary, Business, Rental, Investment
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), default="Monthly")  # Monthly, Annual

    profile = relationship("FinancialProfile", back_populates="income_sources")


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., Rent, Groceries, Utilities
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Essential")  # Essential, Discretionary, EMI
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    is_essential: Mapped[bool] = mapped_column(Boolean, default=True)

    profile = relationship("FinancialProfile", back_populates="expense_items")


class AssetItem(Base):
    __tablename__ = "asset_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., Savings Account, Mutual Funds, Gold
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Liquid")  # Liquid, Fixed Income, Real Estate, Equity
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    liquidity_tier: Mapped[str] = mapped_column(String(20), default="High")  # High, Medium, Low

    profile = relationship("FinancialProfile", back_populates="asset_items")


class LiabilityItem(Base):
    __tablename__ = "liability_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., Home Loan, Car Loan
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Loan")  # Home Loan, Car Loan, Personal Loan, Credit Card
    principal_outstanding: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    monthly_emi: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    interest_rate_pct: Mapped[float] = mapped_column(Numeric(8, 4), default=8.50)
    tenure_months_left: Mapped[int] = mapped_column(Integer, default=60)

    profile = relationship("FinancialProfile", back_populates="liability_items")


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., House Down Payment, Retirement, Higher Ed
    target_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    current_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0.00)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Numeric(8, 4), default=10.00)
    priority: Mapped[str] = mapped_column(String(20), default="High")  # High, Medium, Low

    profile = relationship("FinancialProfile", back_populates="goals")


class FinancialProfileSnapshot(Base):
    __tablename__ = "financial_profile_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    monthly_income: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    monthly_expenses: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_assets: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    total_liabilities: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    profile_data_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    user = relationship("User", back_populates="snapshots")
