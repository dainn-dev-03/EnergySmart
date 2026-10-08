import logging
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.exceptions import NotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)


class ChatRepository:
    def __init__(self, database: Database[dict[str, Any]]) -> None:
        self.conversations = database["chat_conversations"]
        self.turns = database["chat_turns"]

    def list_conversations(self, user_id: int) -> list[dict[str, Any]]:
        try:
            documents = self.conversations.find({"user_id": user_id}).sort(
                [("updated_at", -1), ("_id", -1)]
            ).limit(100)
            return [self._conversation(document) for document in documents]
        except PyMongoError as exc:
            raise self._unavailable(exc) from exc

    def create_conversation(self, user_id: int) -> dict[str, Any]:
        now = datetime.now(UTC)
        document = {
            "user_id": user_id,
            "title": "Cuộc trò chuyện mới",
            "created_at": now,
            "updated_at": now,
        }
        try:
            result = self.conversations.insert_one(document)
            document["_id"] = result.inserted_id
            return self._conversation(document)
        except PyMongoError as exc:
            raise self._unavailable(exc) from exc

    def get_conversation(self, user_id: int, conversation_id: str) -> dict[str, Any]:
        if not ObjectId.is_valid(conversation_id):
            raise NotFoundError("Không tìm thấy cuộc trò chuyện")
        try:
            document = self.conversations.find_one(
                {"_id": ObjectId(conversation_id), "user_id": user_id}
            )
            if document is None:
                raise NotFoundError("Không tìm thấy cuộc trò chuyện")
            return self._conversation(document)
        except PyMongoError as exc:
            raise self._unavailable(exc) from exc

    def get_recent_turns(
        self, user_id: int, conversation_id: str, limit: int
    ) -> list[dict[str, Any]]:
        conversation_object_id = ObjectId(conversation_id)
        try:
            documents = (
                self.turns.find(
                    {"user_id": user_id, "conversation_id": conversation_object_id}
                )
                .sort("_id", -1)
                .limit(limit)
            )
            return list(reversed(list(documents)))
        except PyMongoError as exc:
            raise self._unavailable(exc) from exc

    def list_turns(self, user_id: int, conversation_id: str) -> list[dict[str, Any]]:
        conversation_object_id = ObjectId(conversation_id)
        try:
            documents = self.turns.find(
                {"user_id": user_id, "conversation_id": conversation_object_id}
            ).sort("_id", 1)
            return list(documents)
        except PyMongoError as exc:
            raise self._unavailable(exc) from exc

    def append_turn(
        self,
        user_id: int,
        conversation_id: str,
        user_content: str,
        assistant_content: str,
        visualization: dict[str, Any] | None = None,
    ) -> None:
        conversation_object_id = ObjectId(conversation_id)
        now = datetime.now(UTC)
        try:
            title_filter = {
                "_id": conversation_object_id,
                "user_id": user_id,
                "title": "Cuộc trò chuyện mới",
            }
            update: dict[str, Any] = {"$set": {"updated_at": now}}
            if self.conversations.find_one(title_filter, {"_id": 1}) is not None:
                update["$set"]["title"] = (
                    user_content[:117] + "..." if len(user_content) > 120 else user_content
                )

            assistant_message: dict[str, Any] = {
                "role": "model",
                "content": assistant_content,
            }
            if visualization is not None:
                assistant_message["visualization"] = visualization
            turn = self.turns.insert_one(
                {
                    "user_id": user_id,
                    "conversation_id": conversation_object_id,
                    "messages": [
                        {"role": "user", "content": user_content},
                        assistant_message,
                    ],
                    "created_at": now,
                }
            )
            result = self.conversations.update_one(
                {"_id": conversation_object_id, "user_id": user_id},
                update,
            )
            if result.matched_count != 1:
                self.turns.delete_one({"_id": turn.inserted_id})
                raise NotFoundError("Không tìm thấy cuộc trò chuyện")
        except PyMongoError as exc:
            raise self._unavailable(exc) from exc

    def delete_conversation(self, user_id: int, conversation_id: str) -> None:
        if not ObjectId.is_valid(conversation_id):
            raise NotFoundError("Không tìm thấy cuộc trò chuyện")
        conversation_object_id = ObjectId(conversation_id)
        try:
            result = self.conversations.delete_one(
                {"_id": conversation_object_id, "user_id": user_id}
            )
            if result.deleted_count != 1:
                raise NotFoundError("Không tìm thấy cuộc trò chuyện")
            self.turns.delete_many(
                {"user_id": user_id, "conversation_id": conversation_object_id}
            )
        except PyMongoError as exc:
            raise self._unavailable(exc) from exc

    @staticmethod
    def _conversation(document: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(document["_id"]),
            "user_id": document["user_id"],
            "title": document["title"],
            "created_at": document["created_at"],
            "updated_at": document["updated_at"],
        }

    @staticmethod
    def _unavailable(error: PyMongoError) -> ServiceUnavailableError:
        logger.error("MongoDB chat storage operation failed: %s", type(error).__name__)
        return ServiceUnavailableError("Không thể truy cập lịch sử chat trong MongoDB.")
