"""
utils/logger.py

Simple in-memory cleaning log. Every cleaning module calls `log()` on a
shared CleaningLogger instance so the whole pipeline stays auditable,
exactly like the "Cleaning Log" panel described in the architecture doc.
"""

from datetime import datetime


class CleaningLogger:
    def __init__(self):
        self.entries = []

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.entries.append({"time": timestamp, "message": message})

    def as_text(self) -> str:
        return "\n".join(f"{e['time']}  {e['message']}" for e in self.entries)

    def as_list(self):
        return list(self.entries)

    def clear(self):
        self.entries = []
