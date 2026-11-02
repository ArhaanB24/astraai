import jwt
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserCreate


import bcrypt

class AuthService:
    """
    Abstracted authentication service.
    Supports Local JWT authentication with bcrypt password hashing.
    """

    @staticmethod
    def get_password_hash(password: str) -> str:
        pwd_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not hashed_password or not plain_password:
            return False
        pwd_bytes = plain_password.encode("utf-8")[:72]
        try:
            if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
                return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
            # Legacy sha256 fallback
            salt = "arthaai_salt_123"
            return hashlib.sha256((plain_password + salt).encode("utf-8")).hexdigest() == hashed_password
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        db_user = db.query(User).filter(User.email == user_in.email.lower()).first()
        if db_user:
            raise ValueError("User with this email already exists.")

        hashed = AuthService.get_password_hash(user_in.password)
        new_user = User(
            email=user_in.email.lower(),
            hashed_password=hashed,
            full_name=user_in.full_name,
            onboarding_completed=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        
        # Check if onboarding was completed via questionnaires
        if not getattr(user, "onboarding_completed", False):
            from app.models.user_questionnaire import UserQuestionnaire
            q_count = db.query(UserQuestionnaire).filter(UserQuestionnaire.user_id == user.id).count()
            if q_count >= 5:
                user.onboarding_completed = True
                db.commit()
                db.refresh(user)

        return user
