from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

ChatText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    content: ChatText


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: Literal["user", "model"]
    content: str
    created_at: datetime
    visualization: dict[str, Any] | None = None


class ChatConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ChatConversationDetail(ChatConversationRead):
    messages: list[ChatMessageRead]


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    content: ChatText


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
