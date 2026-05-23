from fastapi import APIRouter, Depends

from app.core.security import get_current_active_user
from app.models.schemas import UserContext, QARequest, QAResponse
from app.server import get_qa_server, QAServer

router = APIRouter()


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    data: QARequest,
    server: QAServer = Depends(get_qa_server),
    current_user: UserContext = Depends(get_current_active_user),
):
    """智能问答入口"""
    result = await server.ask_question(current_user, data.question)
    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        intent=result["intent"],
        confidence=result["confidence"],
    )
