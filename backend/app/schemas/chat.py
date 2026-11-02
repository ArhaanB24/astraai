from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CitationSchema(BaseModel):
    document_name: str
    source: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    relevance_score: float
    url: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[CitationSchema] = []
    tools_used: List[str] = []
    context_data: Optional[Dict[str, Any]] = None
    is_out_of_domain: Optional[bool] = False
    suggested_domain: Optional[str] = None
