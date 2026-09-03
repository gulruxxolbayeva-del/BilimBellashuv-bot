import re
from typing import Any


def normalize_text(text: str, rules: dict[str, Any] | None = None) -> str:
    """Normalize answers using creator-selected tolerance rules."""
    rules = rules or {}
    value = str(text or "").lower() if rules.get("case_sensitive", False) is not True else str(text or "")
    if not rules.get("punctuation_sensitive", False):
        value = re.sub(r"[^\w\s]", "", value)
    if not rules.get("spacing_sensitive", False):
        value = re.sub(r"\s+", " ", value).strip()
    return value.strip() if rules.get("spacing_sensitive", False) else value


def check_written_answer(user_answer: str, accepted_answers: list[str], rules: dict[str, Any] | None = None) -> bool:
    """Check a written answer against accepted variants.

    The default is intentionally forgiving for case, punctuation, and repeated
    spaces.  Optional creator rules can make one of those dimensions strict.
    """
    if not user_answer or not accepted_answers:
        return False
    norm_user = normalize_text(user_answer, rules)
    return any(norm_user == normalize_text(accepted, rules) for accepted in accepted_answers if str(accepted).strip())
