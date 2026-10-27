"""Carbon footprint maths for the Green Footprints app.

All emission factors are kg CO2e.
"""

MOSHI = "Moshi"
MOSHI_KG_PER_KM = 0.03
VEG_MEAL_KG = 0.7

LIMITS = {
    "distance_km": (0.0, 100.0),
    "aircon_hours": (0.0, 24.0),
    "meat_meals": (0, 20),
}

TRANSPORT_FACTORS = {
    "Walk": 0.0,
    "Cycle": 0.0,
    "Bus": 0.05,
    "MRT": 0.03,
    "Car": 0.17,
    MOSHI: 8.0,
}

TRANSPORT_EMOJI = {
    "Walk": "🚶",
    "Cycle": "🚴",
    "Bus": "🚌",
    "MRT": "🚇",
    "Car": "🚗",
    MOSHI: "🐱",
}

AIRCON_KG_PER_HOUR = 0.75

MEAL_KG = 2.5


def transport_kg(mode: str, distance_km: float) -> float:
    return TRANSPORT_FACTORS[mode] * max(distance_km, 0.0)


def aircon_kg(hours: float) -> float:
    return AIRCON_KG_PER_HOUR * max(hours, 0.0)


def meals_kg(meat_meals: int) -> float:
    return MEAL_KG * max(meat_meals, 0)


def total_kg(mode: str, distance_km: float, aircon_hours: float, meat_meals: int) -> float:
    return (
        transport_kg(mode, distance_km)
        + aircon_kg(aircon_hours)
        + meals_kg(meat_meals)
    )


def breakdown(mode: str, distance_km: float, aircon_hours: float, meat_meals: int) -> dict:
    return {
        "Getting to school": transport_kg(mode, distance_km),
        "Air-con at home": aircon_kg(aircon_hours),
        "Meat meals": meals_kg(meat_meals),
    }


def rating(kg: float) -> tuple[str, str, str]:
    """Return (headline, message, emoji) for the day's total."""
    if kg <= 3:
        return (
            "Planet hero!",
            "Wow, that's a really light day. Keep it up!",
            "🌍",
        )
    if kg <= 7:
        return (
            "Nice work!",
            "That's about average. One small swap could make it even lower.",
            "🌱",
        )
    if kg <= 12:
        return (
            "Getting there",
            "A bit on the heavy side today — but small changes add up fast.",
            "🌤️",
        )
    return (
        "Big day!",
        "Lots of CO2 today. Don't worry — every day is a chance to start again.",
        "🔥",
    )


def level(kg: float) -> str:
    """Traffic-light band for the day's total: green, amber or red."""
    if kg <= 7:
        return "green"
    if kg <= 12:
        return "amber"
    return "red"


def level_label(kg: float) -> str:
    band = level(kg)
    return {
        "green": "Great day — nice and low",
        "amber": "Middle of the road",
        "red": "High day — lots of CO2",
    }[band]


def tip(mode: str, distance_km: float, aircon_hours: float, meat_meals: int) -> str:
    """Pick the single most useful tip based on what contributed most."""
    parts = breakdown(mode, distance_km, aircon_hours, meat_meals)
    biggest = max(parts, key=parts.get)

    if parts[biggest] <= 0:
        return "You're already travelling, cooling and eating lightly. Today is a great day to tell a friend how easy it is!"

    if biggest == "Getting to school":
        if mode in ("Walk", "Cycle"):
            return f"Walking or cycling is zero-carbon — {TRANSPORT_EMOJI[mode]} keep it up!"
        if mode == "Car":
            return f"Swapping the car for the bus or MRT on just one trip this week saves about {distance_km * (0.17 - 0.05):.1f} kg of CO2."
        return f"Bus and MRT are already low-carbon — try cycling for shorter {distance_km:.0f} km trips to get to zero."

    if biggest == "Air-con at home":
        if aircon_hours >= 8:
            return f"Turning the air-con off for just 1 of your {aircon_hours:.0f} hours saves 0.75 kg of CO2 — try a fan instead."
        return "Set your air-con to 25°C and close the curtains — you'll feel just as cool and save energy."

    if meat_meals >= 2:
        return f"Swapping one of your {meat_meals} meat meals for a vegetarian one saves about 2.5 kg of CO2 — try it just once this week."
    return "One meat-free meal a week already helps. Nice work keeping it low today!"


class InputProblem(Exception):
    """Raised when a field is empty, not a number, or out of range."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


FIELD_LABELS = {
    "mode": "travel",
    "distance_km": "distance",
    "aircon_hours": "air-con hours",
    "meat_meals": "meat meals",
}

FIELD_PROMPTS = {
    "mode": "pick a way to travel",
    "distance_km": "type how far the trip was, like 5 or 5.5",
    "aircon_hours": "type the hours the air-con was on, like 4",
    "meat_meals": "type the number of meat meals, like 1",
}

MAX_KM = LIMITS["distance_km"][1]
MAX_HOURS = LIMITS["aircon_hours"][1]
MAX_MEALS = LIMITS["meat_meals"][1]


def parse_number(raw, field: str, integer: bool = False) -> float:
    """Turn user text into a number, or raise a friendly InputProblem."""
    prompt = FIELD_PROMPTS[field]

    if raw is None or str(raw).strip() == "":
        raise InputProblem(field, f"Oops, the {FIELD_LABELS[field]} box is empty — {prompt}.")

    text = str(raw).strip().replace(",", "")

    if integer:
        if not text.isdigit():
            if text.lstrip("-").isdigit():
                raise InputProblem(field, f"The number of {FIELD_LABELS[field]} can't be below zero — put 0 if there were none.")
            try:
                as_float = float(text)
            except ValueError:
                raise InputProblem(field, f"Hmm, I couldn't read that — {prompt}. Letters and symbols don't work here.") from None
            if as_float.is_integer():
                value = as_float
            else:
                raise InputProblem(field, f"Please use a whole number for {FIELD_LABELS[field]} — no halves, like 1 or 2.")
        else:
            value = float(int(text))
    else:
        try:
            value = float(text)
        except ValueError:
            raise InputProblem(field, f"Hmm, I couldn't read that — {prompt}. Letters and symbols don't work here.") from None

    if value != value or value in (float("inf"), float("-inf")):
        raise InputProblem(field, f"That number is too big to use — {prompt}.")

    if value < 0:
        raise InputProblem(field, f"The {FIELD_LABELS[field]} can't be below zero — put 0 instead.")

    low, high = LIMITS[field]
    if value > high:
        unit = {"distance_km": "km", "aircon_hours": "hours", "meat_meals": "meals"}[field]
        raise InputProblem(field, f"That looks like a lot! Please keep the {FIELD_LABELS[field]} at {high:g} {unit} or less.")

    return value


def parse_form(form) -> dict:
    """Validate every field at once and report all problems together."""
    modes = list(TRANSPORT_FACTORS)
    mode_raw = (form.get("mode") or "").strip()
    problems: list[InputProblem] = []
    values = {}

    confirm = form.get("confirm_high")
    if mode_raw not in modes:
        if mode_raw.strip() or not confirm:
            raise InputProblem("mode", "Please pick how you got to school first — no travel choice was made.")
        mode = MOSHI
        try:
            values["distance_km"] = parse_number(form.get("distance_km"), "distance_km")
            values["aircon_hours"] = max(parse_number(form.get("aircon_hours"), "aircon_hours", integer=True), 12.0)
        except InputProblem:
            raise InputProblem(
                "mode",
                "Moshi needs a distance and some air-con hours first — fill those in and try the joke again!",
            ) from None
        values["meat_meals"] = max(int(parse_number(form.get("meat_meals"), "meat_meals", integer=True)), 3)
    else:
        mode = mode_raw

    if "aircon_hours" not in values:
        values["distance_km"] = _safe_parse(form.get("distance_km"), "distance_km", False, problems)
        values["aircon_hours"] = _safe_parse(form.get("aircon_hours"), "aircon_hours", True, problems)
        values["meat_meals"] = _safe_parse(form.get("meat_meals"), "meat_meals", True, problems)

    if problems:
        raise ValidationError(problems)
    values["meat_meals"] = int(values["meat_meals"])
    values["mode"] = mode
    return values


class ValidationError(Exception):
    def __init__(self, problems: list[InputProblem]):
        super().__init__("Please check your answers")
        self.problems = problems


def _safe_parse(raw, field, integer, problems):
    try:
        return parse_number(raw, field, integer)
    except InputProblem as problem:
        problems.append(problem)
        return None


def what_if(mode: str, distance_km: float, aircon_hours: float, meat_meals: int) -> dict:
    """Compare today against three easy greener swaps."""
    current = total_kg(mode, distance_km, aircon_hours, meat_meals)
    options = []

    if mode not in ("Walk", "Cycle", MOSHI):
        options.append(
            {
                "emoji": "🚶",
                "label": "Walk or cycle instead",
                "kg": total_kg("Cycle", distance_km, aircon_hours, meat_meals),
                "detail": f"All {distance_km:g} km on zero-carbon wheels" if distance_km else "No trip today",
            }
        )

    if aircon_hours > 0:
        cooler = max(aircon_hours - 2, 0)
        options.append(
            {
                "emoji": "❄️",
                "label": "2 hours less air-con",
                "kg": total_kg(mode, distance_km, cooler, meat_meals),
                "detail": f"Down to {cooler:g} hours — try a fan instead",
            }
        )

    if meat_meals > 0:
        fewer = meat_meals - 1
        veg_kg = total_kg(mode, distance_km, aircon_hours, fewer) + VEG_MEAL_KG
        options.append(
            {
                "emoji": "🥗",
                "label": "One veggie meal instead",
                "kg": veg_kg,
                "detail": "Swap one meat meal for a plant-based one",
            }
        )

    for option in options:
        option["saved"] = max(current - option["kg"], 0.0)

    return {"current": current, "options": options}


def badges(total: float, summary: dict, previous_average: float | None) -> list[dict]:
    """Award stickers. Each has a stable id so the UI can animate new ones."""
    earned = []

    if summary["streak"] >= 1:
        earned.append({"id": "first-day", "emoji": "🌱", "label": "Logged today", "note": "Every journey starts somewhere"})
    if summary["streak"] >= 3:
        earned.append({"id": "streak-3", "emoji": "🔥", "label": "3-day streak", "note": "Three days in a row!"})
    if summary["streak"] >= 7:
        earned.append({"id": "streak-7", "emoji": "🏅", "label": "Week warrior", "note": "Seven days straight"})
    if total <= 3:
        earned.append({"id": "hero", "emoji": "🌍", "label": "Planet hero", "note": "3 kg or less in a day"})
    if total <= 7:
        earned.append({"id": "light", "emoji": "🍃", "label": "Light day", "note": "7 kg or less in a day"})
    if previous_average is not None and total < previous_average - 0.5:
        earned.append({"id": "beat-average", "emoji": "📉", "label": "Beat your average", "note": f"Your usual day is {previous_average:.1f} kg"})
    if summary["logged_days"] >= 5 and total <= summary["average_kg"]:
        earned.append({"id": "better-than-week", "emoji": "⭐", "label": "Better than your week", "note": "Ahead of your 7-day average"})

    return earned


def points(total: float, saved_vs_average: float) -> int:
    """Simple encouragement points: lower footprint and beating your average score."""
    base = max(int(round((15 - total) * 10)), 0)
    bonus = int(round(max(saved_vs_average, 0.0) * 20))
    return base + bonus
