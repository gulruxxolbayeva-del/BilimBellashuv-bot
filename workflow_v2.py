from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class PhaseSettings:
    duration_seconds: int
    per_question: bool = False

@dataclass
class CombinedSession:
    quiz: PhaseSettings
    written: PhaseSettings
    phase: str = "quiz"
    state: str = "scheduled"
    quiz_finished: bool = False
    written_finished: bool = False

    def start(self):
        if self.state in {"cancelled", "finished"}:
            raise ValueError("Session cannot be started")
        self.state = "running"
        self.phase = "quiz"

    def finish_quiz(self):
        if self.state != "running" or self.phase != "quiz":
            raise ValueError("Quiz phase is not running")
        self.quiz_finished = True
        self.phase = "written"
        self.state = "written"

    def finish_written(self):
        if self.state != "written" or self.phase != "written":
            raise ValueError("Written phase is not running")
        self.written_finished = True
        self.state = "finished"

    def cancel(self):
        if self.state in {"finished", "cancelled"}:
            raise ValueError("Session cannot be cancelled")
        self.state = "cancelled"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
