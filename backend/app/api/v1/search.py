from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.services.web_search_service import web_search_service
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/search", tags=["Live Internet Search & Research"])


class SearchResearchRequest(BaseModel):
    query: str = Field(..., example="Why is Tata Power down today?")


class SearchResearchResponse(BaseModel):
    query: str
    evidence_sources: List[Dict[str, Any]]
    answer: str


@router.post("/research", response_model=SearchResearchResponse)
def conduct_web_research(
    req: SearchResearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Searches the live internet and uses Gemini AI to synthesize an accurate,
    grounded explanation of market movements, company events, contracts, or financial news.
    """
    return web_search_service.search_and_research(req.query)
