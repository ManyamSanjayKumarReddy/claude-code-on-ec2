from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import run_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    try:
        reply = await run_chat(payload.message)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return ChatResponse(reply=reply)
