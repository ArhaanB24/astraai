from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.mutual_funds import router as mf_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.finance import router as finance_router
from app.api.v1.chat import router as chat_router
from app.api.v1.search import router as search_router
from app.api.v1.tax import router as tax_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(mf_router)
api_router.include_router(portfolio_router)
api_router.include_router(finance_router)
api_router.include_router(chat_router)
api_router.include_router(search_router)
api_router.include_router(tax_router)
