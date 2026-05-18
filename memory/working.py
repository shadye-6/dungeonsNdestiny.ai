from collections import deque


class WorkingMemory:
    """Short-term memory buffer — holds the last N turn summaries for immediate context."""

    def __init__(self, limit: int = 5):
        self._buffer = deque(maxlen=limit)

    def push(self, summary: str):
        self._buffer.append(summary)

    def get_context(self) -> str:
        return "\n".join(self._buffer)

    def load_from(self, entries: list):
        for entry in entries:
            self._buffer.append(entry)

    def __len__(self) -> int:
        return len(self._buffer)
