"""Chat route — RAG-enhanced conversational interface."""

from __future__ import annotations

from fastapi import APIRouter

from src.analysis.analyzer import chat
from src.api.schemas import ChatRequest, ChatResponse
from src.logging_config import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Ask AlphaRadar anything about stocks using alternative data.

    Examples:
    - "Which semiconductor companies hired the most AI engineers recently?"
    - "Is PLTR's hiring trend bullish?"
    - "Compare SNAP vs META's talent flow"
    """
    response = await chat(
        user_message=request.message,
        history=request.history or None,
        ticker=request.ticker,
    )

    return ChatResponse(
        response=response,
        ticker=request.ticker,
    )
