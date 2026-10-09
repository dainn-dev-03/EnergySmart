from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, settings
from app.repositories.chat_repository import ChatRepository
from app.schemas.analytics import DailyPoint
from app.schemas.chat import ChatMessage, ChatRequest
from app.services.chat_service import (
    MAX_HISTORY_TURNS,
    ChatService,
    ChatStreamEvent,
)


def test_chat_endpoint_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/chat/conversations")

    assert response.status_code == 401


def test_chat_endpoint_reports_missing_gemini_key(
    client: TestClient,
    viewer_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", None)
    service = object.__new__(ChatService)
    service.chats = SimpleNamespace(
        get_conversation=lambda user_id, conversation_id: {"id": conversation_id}
    )
    from app.api.routes.chat import get_chat_service

    client.app.dependency_overrides[get_chat_service] = lambda: service
    response = client.post(
        "/api/v1/chat/conversations/507f1f77bcf86cd799439011/messages",
        headers=viewer_headers,
        json={"content": "Tháng này dùng bao nhiêu điện?"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_chat_request_requires_nonblank_content() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(content="  ")


def test_blank_gemini_key_is_treated_as_unset() -> None:
    configured = Settings.model_validate(
        {
            "jwt_secret_key": "x" * 32,
            "postgres_db": "energy_test",
            "postgres_user": "test",
            "gemini_api_key": "   ",
        }
    )

    assert configured.gemini_api_key is None


def test_blank_mongodb_uri_is_treated_as_unset() -> None:
    configured = Settings.model_validate(
        {
            "jwt_secret_key": "x" * 32,
            "postgres_db": "energy_test",
            "postgres_user": "test",
            "mongodb_uri": " ",
        }
    )

    assert configured.mongodb_uri is None


def _service_for_analytics() -> ChatService:
    service = object.__new__(ChatService)
    service.analytics = SimpleNamespace()
    return service


def test_energy_summary_tool_uses_analytics_service(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _service_for_analytics()
    point = DailyPoint(date=date(2026, 10, 1), kwh=Decimal("12.500"), cost=Decimal("25000"))
    monkeypatch.setattr(service.analytics, "daily", lambda _: [point], raising=False)

    result = service._run_tool("get_energy_summary", {})

    assert result == {
        "from_date": "2026-10-01",
        "to_date": "2026-10-01",
        "total_kwh": 12.5,
        "total_cost": 25000.0,
        "days_in_range": 1,
    }


def test_chat_tools_reject_unknown_arguments() -> None:
    service = _service_for_analytics()

    with pytest.raises(ValueError, match="Unexpected tool arguments"):
        service._run_tool("get_energy_summary", {"sql": "SELECT * FROM electricity_usages"})


def test_agent_allows_general_knowledge_and_keeps_internal_data_scoped() -> None:
    with_tools = ChatService._agent_config(include_tools=True)
    without_tools = ChatService._agent_config(include_tools=False)

    assert "kiến thức phổ thông" in with_tools.system_instruction
    assert "số liệu nội bộ" in with_tools.system_instruction
    assert "Không có quyền truy cập Internet" in with_tools.system_instruction
    assert "hỏi lại ngắn gọn" in with_tools.system_instruction
    assert with_tools.tools
    assert without_tools.tools is None


def test_history_keeps_recent_complete_turns_for_long_conversations() -> None:
    messages = [
        message
        for turn_number in range(MAX_HISTORY_TURNS + 7)
        for message in (
            ChatMessage(role="user", content=f"Câu hỏi {turn_number}"),
            ChatMessage(role="model", content=f"Câu trả lời {turn_number}"),
        )
    ]
    messages.append(ChatMessage(role="user", content="Câu hỏi hiện tại"))

    selected = ChatService._fit_history(messages)

    assert len(selected) == MAX_HISTORY_TURNS * 2 + 1
    assert selected[0].content == "Câu hỏi 7"
    assert selected[-2].content == f"Câu trả lời {MAX_HISTORY_TURNS + 6}"
    assert selected[-1].content == "Câu hỏi hiện tại"
    assert all(
        selected[index].role == "user" and selected[index + 1].role == "model"
        for index in range(0, len(selected) - 1, 2)
    )


def test_stream_reply_sends_saved_conversation_history_to_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conversation_id = "507f1f77bcf86cd799439011"
    saved_turns = [
        {
            "messages": [
                {"role": "user", "content": f"Câu hỏi cũ {turn_number}"},
                {"role": "model", "content": f"Câu trả lời cũ {turn_number}"},
            ]
        }
        for turn_number in range(6)
    ]
    requested_turn_limits: list[int] = []

    class FakeModels:
        def __init__(self) -> None:
            self.planner_contents: list[dict[str, object]] = []

        def generate_content(self, **request: object) -> SimpleNamespace:
            self.planner_contents = cast(list[dict[str, object]], request["contents"])
            return SimpleNamespace(
                candidates=[SimpleNamespace(content=SimpleNamespace(parts=[]))]
            )

        def generate_content_stream(self, **_: object) -> list[SimpleNamespace]:
            return [
                SimpleNamespace(
                    candidates=[
                        SimpleNamespace(
                            content=SimpleNamespace(parts=[SimpleNamespace(text="Đã hiểu.")])
                        )
                    ]
                )
            ]

    class FakeClient:
        def __init__(self) -> None:
            self.models = FakeModels()

        def close(self) -> None:
            pass

    client = FakeClient()
    service = object.__new__(ChatService)
    service.chats = SimpleNamespace(
        get_conversation=lambda user_id, requested_id: {"id": requested_id},
        get_recent_turns=lambda user_id, requested_id, limit: (
            requested_turn_limits.append(limit) or saved_turns[-limit:]
        ),
        append_turn=lambda *_: None,
    )
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("test-key"))
    monkeypatch.setattr("app.services.chat_service.genai.Client", lambda **_: client)

    events = list(
        service.stream_reply(
            conversation_id,
            "Vậy câu trả lời trước đó là gì?",
            cast(Any, SimpleNamespace(id=42)),
        )
    )

    assert requested_turn_limits == [MAX_HISTORY_TURNS]
    assert client.models.planner_contents == [
        message
        for turn_number in range(4, 6)
        for message in (
            {"role": "user", "parts": [{"text": f"Câu hỏi cũ {turn_number}"}]},
            {"role": "model", "parts": [{"text": f"Câu trả lời cũ {turn_number}"}]},
        )
    ] + [
        {"role": "user", "parts": [{"text": "Vậy câu trả lời trước đó là gì?"}]}
    ]
    assert events[-1] == ChatStreamEvent(event="done", conversation_id=conversation_id)


def test_chat_calls_analytics_tool_before_composing_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service_for_analytics()
    point = DailyPoint(date=date(2026, 10, 1), kwh=Decimal("12.500"), cost=Decimal("25000"))
    monkeypatch.setattr(service.analytics, "daily", lambda _: [point], raising=False)

    class FakeModels:
        def __init__(self) -> None:
            self.requests: list[dict[str, object]] = []

        def generate_content(self, **request: object) -> SimpleNamespace:
            self.requests.append(request)
            if len(self.requests) == 1:
                part = SimpleNamespace(
                    function_call=SimpleNamespace(
                        name="get_energy_summary",
                        args={"from_date": "2026-10-01", "to_date": "2026-10-01"},
                    ),
                    text=None,
                )
            else:
                part = SimpleNamespace(function_call=None, text="Đã tiêu thụ 12,5 kWh.")
            content = SimpleNamespace(parts=[part])
            return SimpleNamespace(candidates=[SimpleNamespace(content=content)])

    models = FakeModels()
    answer = service._generate(
        cast(Any, SimpleNamespace(models=models)),
        [ChatMessage(role="user", content="Ngày 1/10 dùng bao nhiêu điện?")],
    )

    assert answer == "Đã tiêu thụ 12,5 kWh."
    assert len(models.requests) == 2
    contents = cast(list[Any], models.requests[1]["contents"])
    tool_response = contents[-1]
    assert tool_response.role == "user"
    assert tool_response.parts[0].function_response.name == "get_energy_summary"


def test_stream_reply_yields_chunks_and_persists_complete_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted_turns: list[tuple[Any, ...]] = []

    class FakeModels:
        def __init__(self) -> None:
            self.planning_calls = 0
            self.requests: list[dict[str, object]] = []

        def generate_content(self, **request: object) -> SimpleNamespace:
            self.planning_calls += 1
            self.requests.append(request)
            parts = (
                [
                    SimpleNamespace(
                        function_call=SimpleNamespace(
                            name="get_consumption_by_floor",
                            args={"from_date": "2026-10-01", "to_date": "2026-10-01"},
                        )
                    )
                ]
                if self.planning_calls == 1
                else []
            )
            return SimpleNamespace(
                candidates=[SimpleNamespace(content=SimpleNamespace(parts=parts))]
            )

        def generate_content_stream(self, **_: object) -> list[SimpleNamespace]:
            return [
                SimpleNamespace(
                    candidates=[
                        SimpleNamespace(
                            content=SimpleNamespace(
                                parts=[SimpleNamespace(text="Tầng 2")]
                            )
                        )
                    ]
                ),
                SimpleNamespace(
                    candidates=[
                        SimpleNamespace(
                            content=SimpleNamespace(
                                parts=[SimpleNamespace(text=" tiêu thụ nhiều nhất.")]
                            )
                        )
                    ]
                ),
            ]

    class FakeClient:
        def __init__(self) -> None:
            self.models = FakeModels()
            self.closed = False

        def close(self) -> None:
            self.closed = True

    client = FakeClient()
    service = object.__new__(ChatService)
    created_conversations: list[int] = []
    service.chats = SimpleNamespace(
        create_conversation=lambda user_id: (
            created_conversations.append(user_id) or {"id": "507f1f77bcf86cd799439012"}
        ),
        get_recent_turns=lambda user_id, conversation_id, limit: [],
        append_turn=lambda *args: persisted_turns.append(args),
    )
    monkeypatch.setattr(
        service,
        "_run_tool",
        lambda name, arguments: {
            "items": [
                {
                    "floor_id": 2,
                    "floor_number": 2,
                    "floor_name": "Tầng 2",
                    "kwh": 12.5,
                    "cost": 25000.0,
                    "share_percent": 100.0,
                }
            ]
        },
    )
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("test-key"))
    monkeypatch.setattr("app.services.chat_service.genai.Client", lambda **_: client)

    chunks = service.stream_reply(
        None,
        "Tầng nào tiêu thụ điện nhiều nhất trong 30 ngày qua?",
        cast(Any, SimpleNamespace(id=42)),
    )
    assert persisted_turns == []
    assert created_conversations == []

    events = list(chunks)
    answer_events = [event for event in events if event.event == "token"]
    status_events = [event for event in events if event.event == "status"]
    visualization_event = next(event for event in events if event.event == "visualization")
    done_event = events[-1]
    assert [event.content for event in answer_events] == [
        "Tầng 2",
        " tiêu thụ nhiều nhất.",
    ]
    assert [event.content for event in status_events] == [
        "Đang xác định dữ liệu cần tra cứu…",
        "Đang tra cứu mức tiêu thụ theo tầng…",
        "Đang tổng hợp câu trả lời…",
    ]
    assert events[0] == status_events[0]
    assert all(event.event == "token" for event in answer_events)
    assert visualization_event.visualization == {
        "floors": {
            "items": [
                {
                    "floor_id": 2,
                    "floor_number": 2,
                    "floor_name": "Tầng 2",
                    "kwh": 12.5,
                    "cost": 25000.0,
                    "share_percent": 100.0,
                }
            ]
        }
    }
    assert done_event == ChatStreamEvent(
        event="done", conversation_id="507f1f77bcf86cd799439012"
    )
    assert created_conversations == [42]
    assert persisted_turns == [
        (
            42,
            "507f1f77bcf86cd799439012",
            "Tầng nào tiêu thụ điện nhiều nhất trong 30 ngày qua?",
            "Tầng 2 tiêu thụ nhiều nhất.",
            {
                "floors": {
                    "items": [
                        {
                            "floor_id": 2,
                            "floor_number": 2,
                            "floor_name": "Tầng 2",
                            "kwh": 12.5,
                            "cost": 25000.0,
                            "share_percent": 100.0,
                        }
                    ]
                }
            },
        )
    ]
    assert client.models.planning_calls == 2
    first_contents = cast(list[Any], client.models.requests[1]["contents"])
    tool_response = first_contents[-1]
    assert tool_response.role == "user"
    assert tool_response.parts[0].function_response.name == "get_consumption_by_floor"
    assert client.closed


def test_chat_message_endpoint_streams_server_sent_events(
    client: TestClient,
    viewer_headers: dict[str, str],
) -> None:
    from app.api.routes.chat import get_chat_service

    service = SimpleNamespace(
        stream_reply=lambda *_: iter(
            [
                ChatStreamEvent(event="token", content="Xin chào"),
                ChatStreamEvent(event="token", content=" bạn!"),
                ChatStreamEvent(
                    event="visualization",
                    visualization={"summary": {"total_kwh": 12.5}},
                ),
                ChatStreamEvent(
                    event="done", conversation_id="507f1f77bcf86cd799439011"
                ),
            ]
        ),
    )
    client.app.dependency_overrides[get_chat_service] = lambda: service

    response = client.post(
        "/api/v1/chat/conversations/507f1f77bcf86cd799439011/messages",
        headers=viewer_headers,
        json={"content": "Xin chào"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'event: token\ndata: {"content": "Xin chào"}\n\n' in response.text
    assert 'event: token\ndata: {"content": " bạn!"}\n\n' in response.text
    assert (
        'event: visualization\ndata: {"visualization": {"summary": {"total_kwh": 12.5}}}\n\n'
        in response.text
    )
    assert 'event: done\ndata: {"conversation_id": "507f1f77bcf86cd799439011"}\n\n' in response.text


def test_new_message_endpoint_streams_without_precreating_conversation(
    client: TestClient,
    viewer_headers: dict[str, str],
) -> None:
    from app.api.routes.chat import get_chat_service

    service = SimpleNamespace(
        stream_reply=lambda conversation_id, *_: (
            iter([ChatStreamEvent(event="done", conversation_id="507f1f77bcf86cd799439012")])
            if conversation_id is None
            else iter([])
        )
    )
    client.app.dependency_overrides[get_chat_service] = lambda: service

    response = client.post(
        "/api/v1/chat/messages",
        headers=viewer_headers,
        json={"content": "Câu hỏi thử", "conversation_id": None},
    )

    assert response.status_code == 200
    assert 'event: done\ndata: {"conversation_id": "507f1f77bcf86cd799439012"}\n\n' in response.text


def test_conversation_lookup_is_scoped_to_its_owner() -> None:
    class FakeCollection:
        def find_one(self, query: dict[str, object]) -> dict[str, object]:
            assert query == {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "user_id": 42,
            }
            return {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "user_id": 42,
                "title": "Điện năng",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }

    repository = ChatRepository(
        cast(Any, {"chat_conversations": FakeCollection(), "chat_turns": object()})
    )
    conversation = repository.get_conversation(42, "507f1f77bcf86cd799439011")

    assert conversation["user_id"] == 42


def test_turn_documents_store_both_messages_and_owner() -> None:
    conversation_id = "507f1f77bcf86cd799439011"
    saved_turns: list[dict[str, object]] = []

    class Conversations:
        def find_one(self, query: dict[str, object], projection: dict[str, int]) -> dict[str, int]:
            assert query["user_id"] == 42
            return {"_id": 1}

        def update_one(
            self, query: dict[str, object], update: dict[str, object]
        ) -> SimpleNamespace:
            assert query["user_id"] == 42
            return SimpleNamespace(matched_count=1)

    class Turns:
        def insert_one(self, document: dict[str, object]) -> None:
            saved_turns.append(document)

    repository = ChatRepository(
        cast(Any, {"chat_conversations": Conversations(), "chat_turns": Turns()})
    )
    repository.append_turn(
        42,
        conversation_id,
        "Tháng này dùng bao nhiêu điện?",
        "Tổng tiêu thụ là 123 kWh.",
        {"summary": {"total_kwh": 123.0}},
    )

    assert saved_turns[0]["user_id"] == 42
    assert saved_turns[0]["conversation_id"] == ObjectId(conversation_id)
    assert saved_turns[0]["messages"] == [
        {"role": "user", "content": "Tháng này dùng bao nhiêu điện?"},
        {
            "role": "model",
            "content": "Tổng tiêu thụ là 123 kWh.",
            "visualization": {"summary": {"total_kwh": 123.0}},
        },
    ]
