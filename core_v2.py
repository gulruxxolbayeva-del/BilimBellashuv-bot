"""BilimBellashuv Bot persistent data and attempt helpers.

The question bank is immutable-by-default and every launch creates a separate
session.  Attempt question order and option order are persisted so a restart
cannot change a participant's test.
"""
from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEST_TYPES = {"quiz", "written", "combined", "single"}
SESSION_STATES = {"draft", "scheduled", "ready", "running", "written", "finished", "cancelled"}
ACTIVE_STATES = ("draft", "scheduled", "ready", "running", "written")


def connect(path: str | Path) -> sqlite3.Connection:
    c = sqlite3.connect(str(path), timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA busy_timeout = 30000")
    return c


def _add_column(c: sqlite3.Connection, table: str, column: str, declaration: str) -> None:
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")
    except sqlite3.OperationalError as exc:
        if "duplicate column name" not in str(exc).lower():
            raise


def init_schema(path: str | Path) -> None:
    c = connect(path)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS quiz_banks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      creator_id INTEGER NOT NULL,
      title TEXT NOT NULL,
      test_type TEXT NOT NULL CHECK(test_type IN ('quiz','written','combined','single')),
      default_settings TEXT NOT NULL DEFAULT '{}',
      active INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS questions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      bank_id INTEGER NOT NULL REFERENCES quiz_banks(id) ON DELETE CASCADE,
      section TEXT NOT NULL DEFAULT 'quiz' CHECK(section IN ('quiz','written')),
      body TEXT NOT NULL,
      image_file_id TEXT,
      options_json TEXT NOT NULL DEFAULT '[]',
      correct_index INTEGER,
      accepted_answers_json TEXT NOT NULL DEFAULT '[]',
      grading_rules_json TEXT NOT NULL DEFAULT '{}',
      points REAL NOT NULL DEFAULT 1,
      position INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      bank_id INTEGER NOT NULL REFERENCES quiz_banks(id) ON DELETE CASCADE,
      creator_id INTEGER NOT NULL,
      code TEXT NOT NULL,
      mode TEXT NOT NULL CHECK(mode IN ('general','single')),
      state TEXT NOT NULL DEFAULT 'draft',
      timezone TEXT NOT NULL DEFAULT 'Asia/Tashkent',
      start_utc TEXT,
      quiz_settings_json TEXT NOT NULL DEFAULT '{}',
      written_settings_json TEXT NOT NULL DEFAULT '{}',
      public_results INTEGER NOT NULL DEFAULT 0,
      cancelled_at TEXT,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE UNIQUE INDEX IF NOT EXISTS active_session_code
      ON sessions(code) WHERE state IN ('draft','scheduled','ready','running','written');
    CREATE TABLE IF NOT EXISTS participants (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      user_id INTEGER NOT NULL,
      display_name TEXT NOT NULL,
      username TEXT,
      ready INTEGER NOT NULL DEFAULT 0,
      phase TEXT NOT NULL DEFAULT 'quiz',
      started_at TEXT,
      finished_at TEXT,
      UNIQUE(session_id, user_id)
    );
    CREATE TABLE IF NOT EXISTS attempts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
      phase TEXT NOT NULL CHECK(phase IN ('quiz','written','single')),
      correct REAL NOT NULL DEFAULT 0,
      wrong REAL NOT NULL DEFAULT 0,
      unanswered REAL NOT NULL DEFAULT 0,
      total_points REAL NOT NULL DEFAULT 0,
      finished_at TEXT,
      is_best INTEGER NOT NULL DEFAULT 0,
      current_position INTEGER NOT NULL DEFAULT 0,
      started_at TEXT,
      deadline_at TEXT
    );
    CREATE TABLE IF NOT EXISTS attempt_questions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
      sequence_no INTEGER NOT NULL,
      question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
      options_order_json TEXT NOT NULL DEFAULT '[]',
      UNIQUE(attempt_id, sequence_no),
      UNIQUE(attempt_id, question_id)
    );
    CREATE TABLE IF NOT EXISTS answers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
      question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
      answer_text TEXT,
      selected_index INTEGER,
      is_correct INTEGER,
      awarded_points REAL NOT NULL DEFAULT 0,
      UNIQUE(attempt_id, question_id)
    );
    CREATE TABLE IF NOT EXISTS certificates (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      participant_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
      pdf_path TEXT,
      sent_at TEXT,
      UNIQUE(session_id, participant_id)
    );
    CREATE INDEX IF NOT EXISTS idx_attempt_questions_attempt ON attempt_questions(attempt_id, sequence_no);
    CREATE INDEX IF NOT EXISTS idx_answers_attempt ON answers(attempt_id);
    CREATE UNIQUE INDEX IF NOT EXISTS one_general_phase_attempt
      ON attempts(participant_id, phase) WHERE phase IN ('quiz','written');
    """)
    # Migrations for databases created by the earlier v2 snapshot.
    _add_column(c, "sessions", "written_ready_at", "TEXT")
    _add_column(c, "sessions", "quiz_finished_at", "TEXT")
    _add_column(c, "attempts", "started_at", "TEXT")
    _add_column(c, "attempts", "deadline_at", "TEXT")
    c.commit()
    c.close()


def make_code(length: int = 8) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(max(4, length)))


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def decode(value: Any, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def active_code_exists(c: sqlite3.Connection, code: str) -> bool:
    return c.execute(
        "SELECT 1 FROM sessions WHERE code=? AND state IN ('draft','scheduled','ready','running','written') LIMIT 1",
        (code.strip(),),
    ).fetchone() is not None


def create_session(c: sqlite3.Connection, bank_id: int, creator_id: int, code: str,
                   mode: str = "general", state: str = "draft", timezone: str = "Asia/Tashkent",
                   start_utc: str | None = None, quiz_settings=None, written_settings=None,
                   public_results: int = 0) -> int:
    if mode not in {"general", "single"}:
        raise ValueError("mode must be general or single")
    code = str(code).strip()
    if len(code) < 3 or len(code) > 64:
        raise ValueError("code length must be between 3 and 64")
    if active_code_exists(c, code):
        raise ValueError("active session code already exists")
    cur = c.execute(
        "INSERT INTO sessions(bank_id,creator_id,code,mode,state,timezone,start_utc,quiz_settings_json,written_settings_json,public_results) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (bank_id, creator_id, code, mode, state, timezone, start_utc,
         encode(quiz_settings or {}), encode(written_settings or {}), int(bool(public_results))),
    )
    return int(cur.lastrowid)


def get_session_by_code(c: sqlite3.Connection, code: str, mode: str | None = None):
    sql = "SELECT * FROM sessions WHERE code=? AND state NOT IN ('cancelled','finished')"
    args: list[Any] = [code.strip()]
    if mode:
        sql += " AND mode=?"
        args.append(mode)
    return c.execute(sql, args).fetchone()


def create_or_get_participant(c: sqlite3.Connection, session_id: int, user_id: int,
                               display_name: str, username: str | None = None) -> int:
    row = c.execute("SELECT id FROM participants WHERE session_id=? AND user_id=?", (session_id, user_id)).fetchone()
    if row:
        c.execute("UPDATE participants SET display_name=?, username=? WHERE id=?", (display_name, username, row["id"]))
        return int(row["id"])
    cur = c.execute(
        "INSERT INTO participants(session_id,user_id,display_name,username) VALUES(?,?,?,?)",
        (session_id, user_id, display_name or "Ishtirokchi", username),
    )
    return int(cur.lastrowid)


def _pick_questions(c: sqlite3.Connection, bank_id: int, phase: str, settings: dict) -> list[sqlite3.Row]:
    section = "quiz" if phase in {"quiz", "single"} else "written"
    rows = c.execute("SELECT * FROM questions WHERE bank_id=? AND section=? ORDER BY position, id", (bank_id, section)).fetchall()
    pick = int(settings.get("pick_count") or len(rows))
    pick = max(0, min(pick, len(rows)))
    selected = list(rows)
    if settings.get("shuffle_questions", settings.get("shuffle") in {"both", "questions"}):
        import random
        random.shuffle(selected)
    return selected[:pick]


def create_attempt(c: sqlite3.Connection, session_id: int, participant_id: int, phase: str,
                   bank_id: int | None = None, settings: dict | None = None) -> int:
    if phase not in {"quiz", "written", "single"}:
        raise ValueError("invalid attempt phase")
    settings = settings or {}
    existing = c.execute(
        "SELECT id FROM attempts WHERE participant_id=? AND phase=? AND finished_at IS NULL ORDER BY id DESC LIMIT 1",
        (participant_id, phase),
    ).fetchone()
    if existing and phase != "single":
        return int(existing["id"])
    if bank_id is None:
        session = c.execute("SELECT bank_id FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not session:
            raise ValueError("session not found")
        bank_id = int(session["bank_id"])
    cur = c.execute(
        "INSERT INTO attempts(session_id,participant_id,phase,started_at) VALUES(?,?,?,?)",
        (session_id, participant_id, phase, iso_now()),
    )
    attempt_id = int(cur.lastrowid)
    rows = _pick_questions(c, bank_id, phase, settings)
    import random
    shuffle_options = bool(settings.get("shuffle_options", settings.get("shuffle") == "both"))
    for seq, q in enumerate(rows):
        indexes = list(range(len(decode(q["options_json"], []))))
        if shuffle_options:
            random.shuffle(indexes)
        c.execute(
            "INSERT INTO attempt_questions(attempt_id,sequence_no,question_id,options_order_json) VALUES(?,?,?,?)",
            (attempt_id, seq, q["id"], encode(indexes)),
        )
    if rows:
        duration_mode = settings.get("duration_mode", "total")
        duration = int(settings.get("duration_seconds") or 0)
        deadline = None
        if duration and duration_mode == "total":
            from datetime import timedelta
            deadline = (datetime.now(timezone.utc) + timedelta(seconds=duration)).isoformat()
        c.execute("UPDATE attempts SET deadline_at=? WHERE id=?", (deadline, attempt_id))
    return attempt_id


def attempt_total(c: sqlite3.Connection, attempt_id: int) -> int:
    row = c.execute("SELECT COUNT(*) AS n FROM attempt_questions WHERE attempt_id=?", (attempt_id,)).fetchone()
    return int(row["n"] if row else 0)


def current_attempt_question(c: sqlite3.Connection, attempt_id: int):
    a = c.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if not a or a["finished_at"]:
        return None
    return c.execute(
        "SELECT aq.*, q.* FROM attempt_questions aq JOIN questions q ON q.id=aq.question_id WHERE aq.attempt_id=? AND aq.sequence_no=?",
        (attempt_id, int(a["current_position"])),
    ).fetchone()


def finish_attempt(c: sqlite3.Connection, attempt_id: int, unanswered: int | None = None) -> bool:
    row = c.execute("SELECT participant_id, current_position FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if not row:
        return False
    total = attempt_total(c, attempt_id)
    answered = int(c.execute("SELECT COUNT(*) AS n FROM answers WHERE attempt_id=?", (attempt_id,)).fetchone()["n"])
    missing = max(0, total - answered) if unanswered is None else max(0, int(unanswered))
    c.execute(
        "UPDATE attempts SET finished_at=COALESCE(finished_at, CURRENT_TIMESTAMP), unanswered=? WHERE id=?",
        (missing, attempt_id),
    )
    # Only the best finished score is official for a participant; ties keep the earlier attempt.
    best = c.execute(
        "SELECT id FROM attempts WHERE participant_id=? AND finished_at IS NOT NULL ORDER BY total_points DESC, correct DESC, id ASC LIMIT 1",
        (row["participant_id"],),
    ).fetchone()
    c.execute("UPDATE attempts SET is_best=0 WHERE participant_id=?", (row["participant_id"],))
    if best:
        c.execute("UPDATE attempts SET is_best=1 WHERE id=?", (best["id"],))
    c.execute("UPDATE participants SET finished_at=COALESCE(finished_at, CURRENT_TIMESTAMP) WHERE id=?", (row["participant_id"],))
    return True


def mark_best_attempt(c: sqlite3.Connection, participant_id: int, attempt_id: int) -> None:
    c.execute("UPDATE attempts SET is_best=0 WHERE participant_id=?", (participant_id,))
    c.execute("UPDATE attempts SET is_best=1 WHERE id=? AND participant_id=?", (attempt_id, participant_id))


def session_is_complete(c: sqlite3.Connection, session_id: int, phase: str) -> bool:
    participants = c.execute("SELECT COUNT(*) AS n FROM participants WHERE session_id=?", (session_id,)).fetchone()["n"]
    finished = c.execute("SELECT COUNT(*) AS n FROM attempts WHERE session_id=? AND phase=? AND finished_at IS NOT NULL", (session_id, phase)).fetchone()["n"]
    return participants > 0 and participants == finished
