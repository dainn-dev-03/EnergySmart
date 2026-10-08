import json
import logging
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, DbSession, get_current_user
from app.core.exceptions import AppError
from app.schemas.chat import (
    ChatConversationDetail,
    ChatConversationRead,
    ChatRequest,
)
from app.schemas.common import ApiResponse
from app.services.chat_service import ChatService, ChatStreamEvent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    dependencies=[Depends(get_current_user)],
)


def get_chat_service(db: DbSession) -> ChatService:
    return ChatService(db)


ServiceDep = Annotated[ChatService, Depends(get_chat_service)]


@router.get(
    "/conversations",
    response_model=ApiResponse[list[ChatConversationRead]],
    summary="Danh sách hội thoại của người dùng hiện tại",
)
def list_conversations(
    service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[list[ChatConversationRead]]:
    return ApiResponse(
        data=[
            ChatConversationRead.model_validate(item)
            for item in service.list_conversations(current_user)
        ]
    )


@router.post(
    "/conversations",
    response_model=ApiResponse[ChatConversationRead],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo cuộc hội thoại mới",
)
def create_conversation(
    service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[ChatConversationRead]:
    return ApiResponse(
        data=ChatConversationRead.model_validate(service.create_conversation(current_user))
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[ChatConversationDetail],
    summary="Chi tiết hội thoại và các message",
)
def get_conversation(
    conversation_id: str, service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[ChatConversationDetail]:
    return ApiResponse(
        data=ChatConversationDetail.model_validate(
            service.get_conversation(conversation_id, current_user)
        )
    )


@router.delete(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[None],
    summary="Xóa hội thoại và các message",
)
def delete_conversation(
    conversation_id: str, service: ServiceDep, current_user: CurrentUser
) -> ApiResponse[None]:
    service.delete_conversation(conversation_id, current_user)
    return ApiResponse(message="Đã xóa cuộc trò chuyện", data=None)


@router.post(
    "/conversations/{conversation_id}/messages",
    summary="Gửi message trong cuộc hội thoại",
)
def send_conversation_message(
    conversation_id: str,
    payload: ChatRequest,
    service: ServiceDep,
    current_user: CurrentUser,
) -> StreamingResponse:
    chunks = service.stream_reply(conversation_id, payload.content, current_user)

    def events() -> Iterator[str]:
        try:
            yield from _serialize_chat_events(chunks)
        except AppError as exc:
            yield (
                "event: error\ndata: "
                f"{json.dumps({'message': exc.message, 'code': exc.code}, ensure_ascii=False)}\n\n"
            )
        except Exception:
            logger.exception("Unexpected error while streaming a chat response")
            error_data = json.dumps(
                {"message": "Không thể hoàn tất câu trả lời.", "code": "INTERNAL_ERROR"},
                ensure_ascii=False,
            )
            yield (
                "event: error\ndata: "
                f"{error_data}\n\n"
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/messages", summary="Gửi message và tạo hội thoại sau khi có câu trả lời")
def send_message(
    payload: ChatRequest,
    service: ServiceDep,
    current_user: CurrentUser,
) -> StreamingResponse:
    chunks = service.stream_reply(
        payload.conversation_id, payload.content, current_user
    )

    def events() -> Iterator[str]:
        try:
            yield from _serialize_chat_events(chunks)
        except AppError as exc:
            error_data = json.dumps(
                {"message": exc.message, "code": exc.code}, ensure_ascii=False
            )
            yield f"event: error\ndata: {error_data}\n\n"
        except Exception:
            logger.exception("Unexpected error while streaming a chat response")
            error_data = json.dumps(
                {"message": "Không thể hoàn tất câu trả lời.", "code": "INTERNAL_ERROR"},
                ensure_ascii=False,
            )
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _serialize_chat_events(chunks: Iterator[ChatStreamEvent]) -> Iterator[str]:
    for chunk in chunks:
        data: dict[str, object] = {}
        if chunk.content is not None:
            data["content"] = chunk.content
        if chunk.conversation_id is not None:
            data["conversation_id"] = chunk.conversation_id
        if chunk.visualization is not None:
            data["visualization"] = chunk.visualization
        yield f"event: {chunk.event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
