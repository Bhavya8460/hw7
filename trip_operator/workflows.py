from __future__ import annotations

from typing import Any

from trip_operator.config import CALENDAR_DIR
from trip_operator.mcp_client import call_tool

TRAVEL_SERVER = "mcp_servers.travel_server"
BUDGET_SERVER = "mcp_servers.budget_server"
CALENDAR_SERVER = "mcp_servers.calendar_server"


async def plan_trip(
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    home_city: str | None = None,
    travelers: int = 1,
    notes: str = "",
    trace: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    snapshot = await call_tool(
        TRAVEL_SERVER,
        "build_trip_snapshot",
        {
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "budget_usd": budget_usd,
            "home_city": home_city,
            "travelers": travelers,
        },
        trace=trace,
    )
    trip = await call_tool(
        BUDGET_SERVER,
        "create_trip_plan",
        {
            "destination": destination,
            "home_city": home_city,
            "start_date": start_date,
            "end_date": end_date,
            "budget_usd": budget_usd,
            "travelers": travelers,
            "planning_snapshot": snapshot,
            "notes": notes,
        },
        trace=trace,
    )
    calendar_path = str(CALENDAR_DIR / f"{trip['trip_id']}.ics")
    calendar = await call_tool(
        CALENDAR_SERVER,
        "build_trip_calendar",
        {
            "trip_id": trip["trip_id"],
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "budget_usd": budget_usd,
            "output_path": calendar_path,
            "planning_snapshot": snapshot,
            "travelers": travelers,
            "notes": notes,
        },
        trace=trace,
    )
    trip = await call_tool(
        BUDGET_SERVER,
        "attach_calendar_path",
        {"trip_id": trip["trip_id"], "calendar_path": calendar["calendar_path"]},
        trace=trace,
    )
    return {"snapshot": snapshot, "trip": trip, "calendar": calendar}


async def get_trip_status(trip_id: str, trace: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    status = await call_tool(BUDGET_SERVER, "get_trip_budget_status", {"trip_id": trip_id}, trace=trace)
    trip = status["trip"]
    weather = await call_tool(
        TRAVEL_SERVER,
        "get_trip_weather",
        {
            "destination": trip["destination"],
            "start_date": trip["start_date"],
            "end_date": trip["end_date"],
        },
        trace=trace,
    )
    reminders = await call_tool(
        CALENDAR_SERVER,
        "preview_trip_calendar",
        {
            "destination": trip["destination"],
            "start_date": trip["start_date"],
            "end_date": trip["end_date"],
            "budget_usd": trip["budget_usd"],
            "planning_snapshot": trip.get("metadata") or {},
            "travelers": trip.get("travelers", 1),
            "notes": trip.get("notes", ""),
        },
        trace=trace,
    )
    return {"status": status, "weather": weather, "reminders": reminders}


async def list_saved_trips(trace: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return await call_tool(BUDGET_SERVER, "list_saved_trips", {}, trace=trace)


async def add_trip_expense(
    trip_id: str,
    expense_date: str,
    category: str,
    amount_usd: float,
    vendor: str = "",
    notes: str = "",
    trace: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return await call_tool(
        BUDGET_SERVER,
        "record_expense",
        {
            "trip_id": trip_id,
            "expense_date": expense_date,
            "category": category,
            "amount_usd": amount_usd,
            "vendor": vendor,
            "notes": notes,
        },
        trace=trace,
    )


async def import_trip_expenses(trip_id: str, csv_path: str, trace: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return await call_tool(
        BUDGET_SERVER,
        "import_expenses_from_csv",
        {"trip_id": trip_id, "csv_path": csv_path},
        trace=trace,
    )
