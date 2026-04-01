from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from trip_operator.config import CALENDAR_DIR
from trip_operator.travel import parse_iso_date, trip_days_and_nights

THEME_KEYWORDS = {
    "culture": {"art", "culture", "gallery", "history", "museum", "architecture"},
    "food": {"brunch", "cafe", "coffee", "culinary", "dining", "food", "market", "restaurant", "street food"},
    "outdoors": {"beach", "hike", "nature", "outdoor", "park", "scenic", "walk"},
    "nightlife": {"bar", "club", "nightlife", "party", "show"},
    "shopping": {"boutique", "mall", "market", "shopping", "souvenir"},
    "relaxation": {"relax", "rest", "slow", "spa", "wellness"},
}

DAY_THEME_LIBRARY = {
    "arrival": {
        "label": "Arrival and orientation",
        "focus": "Settle in quickly and keep the first day light enough to avoid overspending on impulse.",
        "morning": "Handle transit, bag drop, and any must-do check-in steps before adding extra stops.",
        "afternoon": "Take a short orientation walk near the hotel and identify one affordable food option plus the closest transit link.",
        "evening": "Keep dinner casual, confirm tomorrow's route, and stop early so the rest of the trip stays on schedule.",
    },
    "departure": {
        "label": "Departure and wrap-up",
        "focus": "Leave buffer time for checkout, airport transfer, and last expenses instead of cramming in one more paid activity.",
        "morning": "Pack, check out, and use the morning for one short nearby stop only if logistics are already locked in.",
        "afternoon": "Prioritize the transfer window and use spare time for a low-risk cafe break or quick souvenir stop.",
        "evening": "Reconcile receipts, log expenses, and note what worked for the next trip.",
    },
    "landmarks": {
        "label": "Core sights and neighborhoods",
        "focus": "Anchor the day around one headline attraction and one walkable district rather than jumping between distant stops.",
        "morning": "Start with the top-priority landmark or viewpoint before crowds and peak pricing build up.",
        "afternoon": "Move into a nearby neighborhood for lunch, low-cost exploring, and a second lighter stop.",
        "evening": "Keep the evening flexible for a scenic walk, free public space, or an early recharge window.",
    },
    "culture": {
        "label": "Museums and local culture",
        "focus": "Use this day for indoor exhibits, architecture, or history so the plan still works if weather changes.",
        "morning": "Book the main museum, gallery, or cultural site for the first half of the day.",
        "afternoon": "Add a second indoor stop or a slower architecture walk with a budget lunch in between.",
        "evening": "Choose a simple dinner and review whether tomorrow needs reservations or transit passes.",
    },
    "food": {
        "label": "Food crawl and market stops",
        "focus": "Concentrate paid spending on meals that matter and keep the rest of the day easy and walkable.",
        "morning": "Start with a local breakfast or coffee spot near a market, plaza, or other casual morning hub.",
        "afternoon": "Use the afternoon for a market crawl, signature lunch, and one nearby low-cost attraction.",
        "evening": "Reserve the evening for the main meal of the day and skip extra paid entertainment unless budget is ahead.",
    },
    "outdoors": {
        "label": "Parks, viewpoints, and outdoor time",
        "focus": "Put outdoor activities earlier in the day, then keep an indoor backup ready in case the weather slips.",
        "morning": "Use the coolest part of the day for the main park, hike, waterfront, or scenic route.",
        "afternoon": "Break for a low-key lunch and leave enough time for transit back before the day gets expensive.",
        "evening": "Wind down with a simple dinner and avoid stacking another paid activity after the outdoor block.",
    },
    "shopping": {
        "label": "Markets and shopping zones",
        "focus": "Limit shopping to a defined window so souvenirs stay intentional and do not crowd out core trip plans.",
        "morning": "Start with the main market or shopping street while stock is fresh and the area is less crowded.",
        "afternoon": "Cap purchases early, then switch to cafe time or nearby sightseeing instead of drifting into impulse buys.",
        "evening": "Review purchases, set a firm remaining spend cap, and keep the night low-cost.",
    },
    "nightlife": {
        "label": "Shows and evening energy",
        "focus": "Keep the daytime light so there is room for one stronger evening experience without derailing the budget.",
        "morning": "Use the morning for recovery, brunch, and one short low-effort stop near the hotel or transit line.",
        "afternoon": "Keep the afternoon flexible and rest before the evening event, show, or nightlife block.",
        "evening": "Use the main spend here on one planned event, then return without adding multiple paid stops.",
    },
    "relaxation": {
        "label": "Slow day and recovery",
        "focus": "Protect one lower-pressure day so the schedule stays sustainable and the budget has space to recover.",
        "morning": "Take a slower breakfast and use the morning for a park bench, cafe session, or one easy local walk.",
        "afternoon": "Keep the afternoon unstacked with only one optional stop and a clear transit path back.",
        "evening": "Make it an early night with a routine dinner and a quick plan review for the next day.",
    },
}

DEFAULT_THEME_ROTATIONS = {
    "premium": ["landmarks", "culture", "food", "nightlife", "shopping", "relaxation"],
    "standard": ["landmarks", "outdoors", "culture", "food", "nightlife", "relaxation"],
    "value": ["landmarks", "food", "outdoors", "culture", "shopping", "relaxation"],
}

RAIN_SAFE_THEMES = {"culture", "food", "shopping", "relaxation"}


def escape_ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )


def _unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _extract_preferred_themes(notes: str) -> list[str]:
    normalized = notes.lower()
    matches: list[str] = []
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            matches.append(theme)
    return matches


def _choose_day_themes(
    total_days: int,
    cost_tier: str,
    weather: dict[str, Any],
    notes: str,
) -> list[str]:
    preferred = _extract_preferred_themes(notes)
    rotation = DEFAULT_THEME_ROTATIONS.get(cost_tier, DEFAULT_THEME_ROTATIONS["standard"])
    rainy = weather.get("available") and weather.get("rain_risk_days", 0) >= max(2, total_days // 2)

    ordered = _unique_preserving_order(preferred + list(rotation))
    if rainy:
        ordered = [theme for theme in ordered if theme in RAIN_SAFE_THEMES] + [theme for theme in ordered if theme not in RAIN_SAFE_THEMES]
    if not ordered:
        ordered = list(DEFAULT_THEME_ROTATIONS["standard"])
    return ordered


def _budget_style(daily_target_usd: float, travelers: int, within_budget: bool) -> str:
    per_traveler_target = daily_target_usd / max(travelers, 1)
    if not within_budget or per_traveler_target < 90:
        return "tight"
    if per_traveler_target > 180:
        return "comfortable"
    return "balanced"


def _spend_target_for_day(
    day_number: int,
    total_days: int,
    daily_target_usd: float,
    theme: str,
    budget_style: str,
) -> float:
    multiplier = 1.0
    if total_days == 1:
        multiplier = 1.0
    elif day_number == 1:
        multiplier = 0.75
    elif day_number == total_days:
        multiplier = 0.65
    elif theme in {"landmarks", "culture", "outdoors"}:
        multiplier = 1.05 if budget_style != "tight" else 0.95
    elif theme in {"food", "nightlife"}:
        multiplier = 1.0 if budget_style == "comfortable" else 0.9
    elif theme in {"shopping", "relaxation"}:
        multiplier = 0.85
    return round(daily_target_usd * multiplier, 2)


def _build_plan_description(day: dict[str, Any], destination: str, budget_style: str) -> str:
    spend_note = f"Suggested spend cap: ${day['spend_target_usd']:.2f}."
    if budget_style == "tight":
        spend_note += " Keep paid stops intentional and prioritize free public spaces between meals or attractions."
    elif budget_style == "comfortable":
        spend_note += " Use the extra room for one premium stop, but keep the rest of the day lightweight."
    else:
        spend_note += " Keep one paid highlight and let the rest of the day stay flexible."

    return "\n".join(
        [
            f"Suggested plan for {destination}.",
            f"Focus: {day['focus']}",
            f"Morning: {day['morning']}",
            f"Afternoon: {day['afternoon']}",
            f"Evening: {day['evening']}",
            spend_note,
        ]
    )


def build_daily_activity_plan(
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    planning_snapshot: dict[str, Any] | None = None,
    travelers: int = 1,
    notes: str = "",
) -> list[dict[str, Any]]:
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)
    days, _ = trip_days_and_nights(start_date, end_date)
    snapshot = planning_snapshot or {}
    budget_block = snapshot.get("budget") or {}
    assessment = snapshot.get("assessment") or {}
    cost_profile = snapshot.get("cost_profile") or {}
    weather = snapshot.get("weather") or {}

    travelers = int(budget_block.get("travelers") or travelers or 1)
    daily_budget = round(float(budget_block.get("daily_target_usd") or (budget_usd / max(days, 1))), 2)
    cost_tier = str(cost_profile.get("tier") or "standard")
    within_budget = bool(assessment.get("within_budget", True))
    style = _budget_style(daily_budget, travelers, within_budget)
    middle_day_themes = _choose_day_themes(days, cost_tier, weather, notes)

    plan: list[dict[str, Any]] = []
    current = start
    middle_index = 0
    while current <= end:
        day_number = (current - start).days + 1
        if days == 1:
            theme_key = middle_day_themes[0]
        elif day_number == 1:
            theme_key = "arrival"
        elif day_number == days:
            theme_key = "departure"
        else:
            theme_key = middle_day_themes[middle_index % len(middle_day_themes)]
            middle_index += 1

        template = DAY_THEME_LIBRARY[theme_key]
        spend_target = _spend_target_for_day(day_number, days, daily_budget, theme_key, style)
        title = f"Day {day_number} plan: {template['label']}"
        item = {
            "date": current,
            "day_number": day_number,
            "theme": template["label"],
            "title": title,
            "focus": template["focus"],
            "morning": template["morning"],
            "afternoon": template["afternoon"],
            "evening": template["evening"],
            "spend_target_usd": spend_target,
        }
        item["description"] = _build_plan_description(item, destination, style)
        plan.append(item)
        current += timedelta(days=1)
    return plan


def build_trip_events(
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    planning_snapshot: dict[str, Any] | None = None,
    travelers: int = 1,
    notes: str = "",
) -> list[dict[str, Any]]:
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)
    days, _ = trip_days_and_nights(start_date, end_date)
    daily_budget = round(budget_usd / max(days, 1), 2)
    daily_plan = build_daily_activity_plan(
        destination,
        start_date,
        end_date,
        budget_usd,
        planning_snapshot=planning_snapshot,
        travelers=travelers,
        notes=notes,
    )

    events: list[dict[str, Any]] = []
    planning_events = [
        (start - timedelta(days=14), "Lock transport and hotel", f"Book transport and lodging for {destination} while prices are still manageable."),
        (start - timedelta(days=7), "Confirm budget plan", f"Review the trip budget and keep the average daily spend near ${daily_budget:.2f}."),
        (start - timedelta(days=3), "Check weather and pack", f"Refresh weather for {destination} and finalize the packing list."),
        (start - timedelta(days=1), "Check in and prepare transit", f"Complete check-in and prepare documents for the trip to {destination}."),
        (start, "Departure day", f"Trip starts today. Keep day-one spending under ${daily_budget:.2f}."),
    ]
    for event_date, title, description in planning_events:
        events.append({"date": event_date, "title": title, "description": description, "kind": "reminder"})

    for day in daily_plan:
        events.append(
            {
                "date": day["date"],
                "title": day["title"],
                "description": day["description"],
                "kind": "itinerary",
                "day_number": day["day_number"],
                "theme": day["theme"],
            }
        )
        events.append(
            {
                "date": day["date"],
                "title": f"Daily spend check: day {day['day_number']}",
                "description": f"Target no more than ${daily_budget:.2f} in total spend today.",
                "kind": "budget-check",
            }
        )

    events.append(
        {
            "date": end + timedelta(days=1),
            "title": "Reconcile trip expenses",
            "description": f"Log leftover receipts and compare actual spend against the ${budget_usd:.2f} budget.",
            "kind": "reminder",
        }
    )
    return sorted(events, key=lambda item: (item["date"], item["title"]))


def export_ics(events: list[dict[str, Any]], output_path: str | Path) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Trip Budget Operator//EN",
        "CALSCALE:GREGORIAN",
    ]
    for event in events:
        start_token = event["date"].strftime("%Y%m%d")
        end_token = (event["date"] + timedelta(days=1)).strftime("%Y%m%d")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uuid4()}",
                f"DTSTAMP:{timestamp}",
                f"DTSTART;VALUE=DATE:{start_token}",
                f"DTEND;VALUE=DATE:{end_token}",
                f"SUMMARY:{escape_ics_text(event['title'])}",
                f"DESCRIPTION:{escape_ics_text(event['description'])}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def preview_trip_calendar(
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    planning_snapshot: dict[str, Any] | None = None,
    travelers: int = 1,
    notes: str = "",
) -> dict[str, Any]:
    daily_plan = build_daily_activity_plan(
        destination,
        start_date,
        end_date,
        budget_usd,
        planning_snapshot=planning_snapshot,
        travelers=travelers,
        notes=notes,
    )
    return {
        "events": build_trip_events(
            destination,
            start_date,
            end_date,
            budget_usd,
            planning_snapshot=planning_snapshot,
            travelers=travelers,
            notes=notes,
        ),
        "daily_plan": daily_plan,
    }


def build_trip_calendar(
    trip_id: str,
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    output_path: str | None = None,
    planning_snapshot: dict[str, Any] | None = None,
    travelers: int = 1,
    notes: str = "",
) -> dict[str, Any]:
    if output_path is None:
        output_path = CALENDAR_DIR / f"{trip_id}.ics"
    daily_plan = build_daily_activity_plan(
        destination,
        start_date,
        end_date,
        budget_usd,
        planning_snapshot=planning_snapshot,
        travelers=travelers,
        notes=notes,
    )
    events = build_trip_events(
        destination,
        start_date,
        end_date,
        budget_usd,
        planning_snapshot=planning_snapshot,
        travelers=travelers,
        notes=notes,
    )
    calendar_path = export_ics(events, output_path)
    return {"trip_id": trip_id, "calendar_path": calendar_path, "events": events, "daily_plan": daily_plan}
