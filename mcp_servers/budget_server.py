from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from trip_operator.storage import (
    add_expense,
    create_trip_plan,
    get_budget_status,
    import_expenses_from_csv,
    initialize_database,
    list_trips,
    set_calendar_path,
)

initialize_database()

mcp = FastMCP(
    "budget_mcp",
    instructions="Trip budget MCP server backed by SQLite.",
    json_response=True,
    log_level="ERROR",
)


@mcp.tool(name="create_trip_plan")
def create_trip_plan_tool(
    destination: str,
    home_city: str | None,
    start_date: str,
    end_date: str,
    budget_usd: float,
    travelers: int,
    planning_snapshot: dict,
    notes: str = "",
) -> dict:
    """Persist a trip plan and its planning snapshot."""
    return create_trip_plan(destination, home_city, start_date, end_date, budget_usd, travelers, planning_snapshot, notes)


@mcp.tool(name="record_expense")
def record_expense_tool(
    trip_id: str,
    expense_date: str,
    category: str,
    amount_usd: float,
    vendor: str = "",
    notes: str = "",
) -> dict:
    """Record one trip expense."""
    return add_expense(trip_id, expense_date, category, amount_usd, vendor, notes)


@mcp.tool(name="import_expenses_from_csv")
def import_expenses_from_csv_tool(trip_id: str, csv_path: str) -> dict:
    """Bulk import expenses from a CSV file."""
    return import_expenses_from_csv(trip_id, csv_path)


@mcp.tool(name="get_trip_budget_status")
def get_trip_budget_status_tool(trip_id: str) -> dict:
    """Return current budget status and expense breakdown."""
    return get_budget_status(trip_id)


@mcp.tool(name="list_saved_trips")
def list_saved_trips_tool() -> dict:
    """List all saved trips."""
    return {"trips": list_trips()}


@mcp.tool(name="attach_calendar_path")
def attach_calendar_path_tool(trip_id: str, calendar_path: str) -> dict:
    """Attach the generated calendar path to a trip."""
    return set_calendar_path(trip_id, calendar_path)


if __name__ == "__main__":
    mcp.run(transport="stdio")
