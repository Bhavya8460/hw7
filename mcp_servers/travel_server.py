from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from trip_operator.travel import build_trip_snapshot, get_trip_weather, supported_destinations

mcp = FastMCP(
    "travel_mcp",
    instructions="Trip planning MCP server for geocoding, weather, currency lookup, and budget estimation.",
    json_response=True,
    log_level="ERROR",
)


@mcp.tool(name="build_trip_snapshot")
async def build_trip_snapshot_tool(
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    home_city: str | None = None,
    travelers: int = 1,
) -> dict:
    """Build a live trip planning snapshot with travel and budget estimates."""
    return await build_trip_snapshot(destination, start_date, end_date, budget_usd, home_city, travelers)


@mcp.tool(name="get_trip_weather")
async def get_trip_weather_tool(destination: str, start_date: str, end_date: str) -> dict:
    """Refresh the destination weather window for a trip."""
    return await get_trip_weather(destination, start_date, end_date)


@mcp.tool(name="list_supported_destinations")
def list_supported_destinations_tool() -> dict:
    """List destinations with tuned local cost profiles."""
    return {"destinations": supported_destinations()}


if __name__ == "__main__":
    mcp.run(transport="stdio")
