from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.services.mutual_fund_service import MutualFundService
from app.schemas.mutual_fund import FundSearchResponse, FundDetailResponse, FundHoldingSchema

router = APIRouter(prefix="/mutual-funds", tags=["Mutual Funds"])
mf_service = MutualFundService()


@router.get("/catalog")
def get_funds_catalog():
    """Returns all available/curated mutual funds in the ArthaAI system."""
    return mf_service.get_available_catalog()


@router.get("/search", response_model=List[FundSearchResponse])
def search_funds(q: str):
    if not q or len(q.strip()) < 1:
        return mf_service.get_available_catalog()[:10]
    return mf_service.search_funds(q.strip())


@router.get("/{scheme_code}", response_model=FundDetailResponse)
def get_fund_details(scheme_code: str, db: Session = Depends(get_db)):
    details = mf_service.get_fund_details(db, scheme_code)
    if not details:
        raise HTTPException(status_code=404, detail="Mutual fund scheme not found.")
    return details


@router.get("/{scheme_code}/nav")
def get_nav_history(scheme_code: str, limit: int = 365):
    return mf_service.get_nav_history(scheme_code, limit=limit)


@router.get("/{scheme_code}/holdings", response_model=List[FundHoldingSchema])
def get_fund_holdings(scheme_code: str):
    return mf_service.get_holdings(scheme_code)
