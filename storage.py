"""Local daily history storage for Green Footprints.

A tiny JSON file keeps one entry per day. No accounts, no database,
no personal data beyond the numbers the student already typed.
"""

import json
import os
import tempfile
from datetime import date, timedelta

DATA_DIR = os.environ.get("GREEN_FOOTPRINTS_DATA", os.path.join(os.path.dirname(__file__), "data"))
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")

MAX_DAYS_KEPT = 120


def _ensure_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_history(user_id: str = "local") -> dict:
    """Return {date_str: entry} for this user."""
    if not os.path.exists(HISTORY_PATH):
        return {}
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}
    return raw.get(user_id, {})


def _write_all(all_users: dict) -> None:
    _ensure_dir()
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(all_users, fh, indent=2)
        os.replace(tmp, HISTORY_PATH)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def save_day(entry: dict, user_id: str = "local", day: date | None = None) -> dict:
    """Save (or overwrite) one day's entry. Returns the saved entry."""
    day = day or date.today()
    key = day.isoformat()

    all_users = {}
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as fh:
            all_users = json.load(fh)

    user = all_users.setdefault(user_id, {})
    record = dict(entry)
    record["date"] = key
    user[key] = record

    for old in sorted(user)[:-MAX_DAYS_KEPT]:
        del user[old]

    _write_all(all_users)
    return record


def last_n_days(history: dict, n: int = 7, today: date | None = None) -> list[dict]:
    """Oldest-to-newest list of the last n days, with gaps marked as missing."""
    today = today or date.today()
    out = []
    for offset in range(n - 1, -1, -1):
        day = today - timedelta(days=offset)
        key = day.isoformat()
        entry = history.get(key)
        out.append(
            {
                "date": key,
                "label": day.strftime("%a"),
                "day_number": day.day,
                "kg": entry.get("kg") if entry else None,
                "is_today": offset == 0,
            }
        )
    return out


def streak(history: dict, today: date | None = None) -> int:
    """Count back from today while consecutive days have entries."""
    today = today or date.today()
    count = 0
    while True:
        key = (today - timedelta(days=count)).isoformat()
        if key not in history:
            return count
        count += 1


def week_summary(history: dict, today: date | None = None) -> dict:
    """Totals for the last 7 days including any gap days as zero."""
    days = last_n_days(history, 7, today)
    values = [d["kg"] for d in days if d["kg"] is not None]
    logged = len(values)
    total = sum(values)
    average = total / logged if logged else 0.0
    return {
        "days": days,
        "logged_days": logged,
        "total_kg": total,
        "average_kg": average,
        "best_day": min(values) if values else None,
        "streak": streak(history, today),
    }


def average_all(history: dict) -> float | None:
    values = [e["kg"] for e in history.values() if e.get("kg") is not None]
    return sum(values) / len(values) if values else None
