import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    request_id: Mapped[str] = mapped_column(String(100), nullable=True)

    tools_used_json: Mapped[dict] = mapped_column(JSON, default=list)
    engines_used_json: Mapped[dict] = mapped_column(JSON, default=list)
    retrieved_docs_json: Mapped[dict] = mapped_column(JSON, default=list)

    execution_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS")  # SUCCESS, ERROR
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
