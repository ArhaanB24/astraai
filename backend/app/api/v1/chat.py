from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.mutual_fund_agent import mutual_fund_agent
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage

router = APIRouter(prefix="/chat", tags=["Mutual Fund AI Chat"])


@router.post("", response_model=ChatResponse)
@router.post("/message", response_model=ChatResponse)
def chat_with_mutual_fund_agent(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get or create chat session
    session_id = req.session_id
    if not session_id:
        session = ChatSession(user_id=current_user.id, title="Mutual Fund Advisory")
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id

    # Record User Message
    user_msg = ChatMessage(session_id=session_id, sender="user", content=req.message)
    db.add(user_msg)
    db.commit()

    # Fetch recent conversation history for follow-up resolution
    prev_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(20).all()
    history = [{"role": m.sender, "content": m.content} for m in reversed(prev_messages)]

    # Process via Agent
    agent_res = mutual_fund_agent.process_query(db, current_user.id, req.message, conversation_history=history)

    # Record Assistant Message
    assistant_msg = ChatMessage(
        session_id=session_id,
        sender="assistant",
        content=agent_res["answer"],
        tool_calls_json=agent_res["tools_used"]
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        answer=agent_res["answer"],
        citations=agent_res["citations"],
        tools_used=agent_res["tools_used"],
        context_data=agent_res.get("context_data"),
        is_out_of_domain=agent_res.get("is_out_of_domain", False),
        suggested_domain=agent_res.get("suggested_domain")
    )
