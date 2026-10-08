from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError


@lru_cache
def get_chat_database() -> Database[dict[str, object]]:
    if settings.mongodb_uri is None:
        raise ServiceUnavailableError(
            "Chatbot chưa được cấu hình. Hãy đặt MONGODB_URI trong backend/.env"
        )
    client: MongoClient[dict[str, object]] = MongoClient(
        settings.mongodb_uri.get_secret_value(),
        serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
        tz_aware=True,
    )
    try:
        database = client[settings.mongodb_database]
        database.command("ping")
        database["chat_conversations"].create_index(
            [("user_id", 1), ("updated_at", -1)]
        )
        database["chat_turns"].create_index(
            [("conversation_id", 1), ("_id", -1)]
        )
        database["chat_turns"].create_index([("user_id", 1), ("conversation_id", 1)])
        return database
    except PyMongoError as exc:
        client.close()
        raise ServiceUnavailableError("Không thể kết nối MongoDB để lưu lịch sử chatbot.") from exc


def close_chat_database() -> None:
    if get_chat_database.cache_info().currsize:
        get_chat_database().client.close()
    get_chat_database.cache_clear()
