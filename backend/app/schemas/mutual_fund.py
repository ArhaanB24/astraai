from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class FundSearchResponse(BaseModel):
    scheme_code: str
    scheme_name: str


class FundDetailResponse(BaseModel):
    scheme_code: str
    scheme_name: str
    fund_house: Optional[str] = None
    category: Optional[str] = None
    scheme_type: Optional[str] = None
    current_nav: Optional[float] = None
    nav_date: Optional[str] = None


class FundHoldingSchema(BaseModel):
    company_name: str
    sector: Optional[str] = None
    allocation_percentage: float
