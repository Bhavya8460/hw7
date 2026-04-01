from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from trip_operator.calendaring import build_trip_calendar, preview_trip_calendar

mcp = FastMCP(
    "calendar_mcp",
    instructions="Trip reminder and iCalendar export MCP server.",
    json_response=True,
    log_level="ERROR",
)


@mcp.tool(name="preview_trip_calendar")
def preview_trip_calendar_tool(
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    planning_snapshot: dict | None = None,
    travelers: int = 1,
    notes: str = "",
) -> dict:
    """Preview reminder events and day-by-day suggestions for a trip."""
    return preview_trip_calendar(destination, start_date, end_date, budget_usd, planning_snapshot, travelers, notes)


@mcp.tool(name="build_trip_calendar")
def build_trip_calendar_tool(
    trip_id: str,
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    output_path: str | None = None,
    planning_snapshot: dict | None = None,
    travelers: int = 1,
    notes: str = "",
) -> dict:
    """Generate an .ics file with reminders and a suggested day-by-day plan."""
    return build_trip_calendar(trip_id, destination, start_date, end_date, budget_usd, output_path, planning_snapshot, travelers, notes)


if __name__ == "__main__":
    mcp.run(transport="stdio")
