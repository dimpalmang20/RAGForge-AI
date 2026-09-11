from collections import defaultdict

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory


class InMemorySessionStore:
    def __init__(self, max_messages: int = 10) -> None:
        self._store: dict[str, InMemoryChatMessageHistory] = defaultdict(InMemoryChatMessageHistory)
        self._max_messages = max_messages

    def _key(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def get_history(self, user_id: str, session_id: str) -> BaseChatMessageHistory:
        return self._store[self._key(user_id, session_id)]

    def get_history_by_key(self, session_key: str) -> BaseChatMessageHistory:
        return self._store[session_key]

    def trim_history(self, user_id: str, session_id: str) -> None:
        history = self.get_history(user_id=user_id, session_id=session_id)
        if len(history.messages) > self._max_messages:
            history.messages = history.messages[-self._max_messages :]

    def clear_history(self, user_id: str, session_id: str) -> None:
        self._store.pop(self._key(user_id, session_id), None)

    def clear_user_histories(self, user_id: str) -> int:
        keys_to_delete = [key for key in self._store if key.startswith(f"{user_id}:")]
        for key in keys_to_delete:
            self._store.pop(key, None)
        return len(keys_to_delete)


session_store = InMemorySessionStore()