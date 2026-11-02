from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.profile import FinancialProfileCreate, FinancialProfileResponse
from app.schemas.questionnaire import QuestionnaireSubmission, QuestionnaireResponse
from app.services.profile_service import ProfileService
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/profile", tags=["Financial Profile"])


@router.get("", response_model=FinancialProfileResponse)
@router.get("/current", response_model=FinancialProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ProfileService.get_or_create_profile(db, current_user.id)


@router.put("", response_model=FinancialProfileResponse)
def update_profile(
    profile_in: FinancialProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProfileService.update_profile(db, current_user.id, profile_in)


@router.post("/questionnaire", response_model=FinancialProfileResponse)
def save_questionnaire(
    submission: QuestionnaireSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProfileService.save_questionnaire(db, current_user.id, submission)


@router.get("/questionnaire", response_model=List[QuestionnaireResponse])
def get_questionnaire(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ProfileService.get_questionnaire(db, current_user.id)


@router.get("/dossier")
def get_user_dossier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.user_profiler_service import user_profiler_service
    return user_profiler_service.get_user_dossier(db, current_user.id)


