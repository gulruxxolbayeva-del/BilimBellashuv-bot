from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from core_v2 import connect, create_or_get_participant, create_session, encode, make_code

DEFAULT_TZ = "Asia/Tashkent"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _settings(raw: dict, default_pick: int, question_count: int) -> dict:
    raw = raw or {}
    mode = raw.get("duration_mode", raw.get("durationMode", "total"))
    value = _safe_int(raw.get("duration_seconds", raw.get("duration", 0)), 0)
    if mode == "total" and "duration_seconds" not in raw:
        value *= 60
    return {
        "pick_count": max(1, min(_safe_int(raw.get("pick_count", raw.get("pick", default_pick)), default_pick), question_count)),
        "shuffle_questions": bool(raw.get("shuffle_questions", raw.get("shuffle") in {"both", "questions"})),
        "shuffle_options": bool(raw.get("shuffle_options", raw.get("shuffle") == "both")),
        "duration_mode": mode if mode in {"total", "question"} else "total",
        "duration_seconds": max(0, value),
        "certificate_enabled": bool(raw.get("certificate_enabled", False)),
        "certificate_threshold": float(raw.get("certificate_threshold", 0) or 0),
        "certificate_threshold_type": raw.get("certificate_threshold_type", "points"),
        "certificate_text": str(raw.get("certificate_text", ""))[:1000],
        "public_results": bool(raw.get("public_results", False)),
    }


def save_test_payload(db_path: str, user_id: int, payload: dict) -> dict:
    title = str(payload.get("title", "")).strip()[:200]
    questions = payload.get("questions") or []
    test_type = str(payload.get("type", "quiz"))
    if not title or not (1 <= len(questions) <= 2000) or test_type not in {"quiz", "written", "combined", "single"}:
        raise ValueError("Test nomi, turi yoki savollar noto‘g‘ri")

    session_info = payload.get("session") or {}
    code = str(session_info.get("code", "")).strip() or make_code(8)
    tz_name = str(session_info.get("timezone") or payload.get("timezone") or DEFAULT_TZ).split(" — ", 1)[0]
    ZoneInfo(tz_name)
    start_utc = None
    if test_type != "single":
        local_value = str(session_info.get("start_local", "")).strip()
        if not local_value:
            raise ValueError("Boshlanish vaqti kiritilmagan")
        start_dt = datetime.fromisoformat(local_value).replace(tzinfo=ZoneInfo(tz_name)).astimezone(timezone.utc)
        if start_dt <= _now_utc() + timedelta(minutes=5):
            raise ValueError("Boshlanish vaqti kamida 5 daqiqa keyin bo‘lishi kerak")
        start_utc = start_dt.isoformat()

    c = connect(db_path)
    try:
        c.execute("BEGIN IMMEDIATE")
        bank_id = c.execute(
            "INSERT INTO quiz_banks(creator_id,title,test_type,default_settings) VALUES(?,?,?,?)",
            (int(user_id), title, test_type, encode(payload)),
        ).lastrowid
        quiz_count = written_count = 0
        for pos, item in enumerate(questions):
            body = str(item.get("text", "")).strip()
            options = [str(x).strip() for x in (item.get("options") or []) if str(x).strip()]
            if not body:
                raise ValueError("Bo‘sh savol bor")
            section = str(item.get("section") or ("written" if test_type == "written" else "quiz"))
            section = "written" if section == "written" and test_type in {"written", "combined"} else "quiz"
            correct = None
            if section == "quiz":
                if not 2 <= len(options) <= 4:
                    raise ValueError("Quiz savolida 2–4 ta variant bo‘lishi kerak")
                correct = _safe_int(item.get("correct"), -1)
                if not 0 <= correct < len(options):
                    raise ValueError("To‘g‘ri javob tanlanmagan")
                quiz_count += 1
            else:
                written_count += 1
            accepted = item.get("accepted", [])
            if isinstance(accepted, str):
                accepted = [x.strip() for x in re.split(r"[,;\n]", accepted) if x.strip()]
            c.execute(
                "INSERT INTO questions(bank_id,section,body,image_file_id,options_json,correct_index,accepted_answers_json,grading_rules_json,points,position) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (bank_id, section, body, str(item.get("image_url", item.get("image_file_id", "")) or "").strip()[:1000] or None,
                 encode(options), correct, encode(accepted), encode(item.get("grading_rules", {})), max(0, float(item.get("points", 1) or 1)), pos),
            )
        if (test_type in {"quiz", "single"} and not quiz_count) or (test_type == "written" and not written_count) or (test_type == "combined" and (not quiz_count or not written_count)):
            raise ValueError("Test qismlari to‘liq emas")
        quiz_settings = _settings(payload.get("quiz_settings") or payload, quiz_count or len(questions), quiz_count or len(questions))
        written_settings = _settings(payload.get("written_settings") or payload, written_count or len(questions), written_count or len(questions))
        mode = "single" if test_type == "single" else "general"
        state = "running" if mode == "single" else "scheduled"
        session_id = create_session(
            c, bank_id, int(user_id), code, mode=mode, state=state, timezone=tz_name,
            start_utc=start_utc, quiz_settings=quiz_settings, written_settings=written_settings,
            public_results=int(bool(session_info.get("public_results", payload.get("public_results", False)))),
        )
        participant_id = None
        if mode == "general" and session_info.get("creator_participates"):
            participant_id = create_or_get_participant(c, session_id, int(user_id), str(payload.get("creator_name") or "Yaratuvchi"), payload.get("creator_username"))
        c.commit()
        return {"title": title, "code": code, "mode": mode, "session_id": int(session_id), "participant_id": participant_id}
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
