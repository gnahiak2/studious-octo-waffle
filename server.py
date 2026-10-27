"""Green Footprints — a friendly carbon footprint website for students.

Run locally:  python3 server.py
"""

import os
from datetime import date

from flask import Flask, jsonify, render_template, request

import carbon
import storage

app = Flask(__name__)


def _client_id() -> str:
    """Keep each browser's history separate without any sign-up."""
    raw = request.cookies.get("gf_id", "local")
    clean = "".join(ch for ch in raw if ch.isalnum() or ch in "-_")[:40]
    return clean or "local"


def _build_page(state: dict, status: int = 200):
    response = app.make_response((render_template("index.html", **state), status))
    if "gf_id" not in request.cookies:
        response.set_cookie("gf_id", os.urandom(8).hex(), max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response


def _empty_state():
    today = date.today()
    return {
        "form": {"mode": "Walk", "distance_km": "5", "aircon_hours": "4", "meat_meals": "1"},
        "errors": [],
        "summary_line": "",
        "result": None,
        "week": None,
        "badges": [],
        "points_total": 0,
        "confirmed": False,
        "mystery": False,
        "form_error_fields": {},
        "today_label": today.strftime("%A %d %B"),
    }


def _week_payload(history: dict) -> dict:
    summary = storage.week_summary(history)
    peak = max([d["kg"] for d in summary["days"] if d["kg"] is not None] or [1.0]) or 1.0
    days = []
    for day in summary["days"]:
        pct = 0.0 if day["kg"] is None else max(round(day["kg"] / peak * 100, 1), 6.0)
        days.append({**day, "percent": pct})
    return {
        "days": days,
        "logged_days": summary["logged_days"],
        "total_kg": round(summary["total_kg"], 1),
        "average_kg": round(summary["average_kg"], 1),
        "best_day": None if summary["best_day"] is None else round(summary["best_day"], 1),
        "streak": summary["streak"],
        "has_data": summary["logged_days"] > 0,
    }


@app.get("/")
def index():
    state = _empty_state()
    history = storage.load_history(_client_id())
    state["week"] = _week_payload(history)
    return _build_page(state)


@app.post("/calculate")
def calculate():
    state = _empty_state()
    form = request.form
    client = _client_id()
    history = storage.load_history(client)
    confirmed = form.get("confirm_high") == "1"
    state["confirmed"] = confirmed

    state["form"] = {
        "mode": form.get("mode", "Walk"),
        "distance_km": form.get("distance_km", ""),
        "aircon_hours": form.get("aircon_hours", ""),
        "meat_meals": form.get("meat_meals", ""),
    }

    try:
        values = carbon.parse_form(form)
    except carbon.InputProblem as problem:
        if problem.field == "mode" and form.get("mystery") == "1":
            state["week"] = _week_payload(history)
            state["mystery"] = True
            return _build_page(state, 200)
        state["week"] = _week_payload(history)
        return _build_page(_with_error(state, problem.field, problem.message), 400)
    except carbon.ValidationError as problem_set:
        state["week"] = _week_payload(history)
        state["errors"] = [{"field": p.field, "message": p.message} for p in problem_set.problems]
        state["form_error_fields"] = {p.field: True for p in problem_set.problems}
        return _build_page(state, 400)

    mode = values["mode"]
    distance = values["distance_km"]
    hours = values["aircon_hours"]
    meals = values["meat_meals"]

    total = carbon.total_kg(mode, distance, hours, meals)
    headline, message, emoji = carbon.rating(total)
    parts = carbon.breakdown(mode, distance, hours, meals)
    previous_average = storage.average_all(history)

    saved = storage.save_day(
        {
            "kg": round(total, 2),
            "mode": mode,
            "distance_km": distance,
            "aircon_hours": hours,
            "meat_meals": meals,
        },
        user_id=client,
    )
    history[saved["date"]] = saved

    week = _week_payload(history)
    earned = carbon.badges(total, storage.week_summary(history), previous_average)
    gained = carbon.points(total, (previous_average - total) if previous_average else 0.0)

    state["week"] = week
    state["result"] = {
        "total": round(total, 1),
        "headline": headline,
        "message": message,
        "emoji": emoji,
        "level": carbon.level(total),
        "level_label": carbon.level_label(total),
        "biggest": max(parts, key=parts.get),
        "parts": [
            {"name": name, "kg": round(kg, 1), "percent": round(kg / max(max(parts.values()), 0.001) * 100, 1)}
            for name, kg in parts.items()
        ],
        "tip": carbon.tip(mode, distance, hours, meals),
    }
    state["comparison"] = _comparison_payload(carbon.what_if(mode, distance, hours, meals))
    state["badges"] = earned
    state["points"] = gained
    state["points_total"] = _points_total(history)
    state["share"] = {
        "total": round(total, 1),
        "headline": headline,
        "emoji": emoji,
        "streak": week["streak"],
        "saved": round(max(previous_average - total, 0), 1) if previous_average else None,
        "date_label": date.today().strftime("%d %b"),
        "points": state["points_total"],
    }
    state["today_label"] = date.today().strftime("%A %d %B")
    return _build_page(state)


def _with_error(state: dict, field: str, message: str) -> dict:
    state["errors"] = [{"field": field, "message": message}]
    return state


def _points_total(history: dict) -> int:
    total = 0
    for entry in history.values():
        if entry.get("kg") is None:
            continue
        total += max(int(round((15 - entry["kg"]) * 10)), 0)
    return total


def _comparison_payload(data: dict) -> dict:
    current = data["current"]
    options = data["options"]
    return {
        "current": round(current, 1),
        "options": [
            {
                "emoji": o["emoji"],
                "label": o["label"],
                "kg": round(o["kg"], 1),
                "saved": round(o["saved"], 1),
                "percent": round(max(0.0, (1 - o["kg"] / current) * 100, 0.0), 0) if current > 0 else 0,
                "detail": o["detail"],
            }
            for o in options
        ],
    }


@app.get("/history.json")
def history_json():
    return jsonify(storage.load_history(_client_id()))


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
