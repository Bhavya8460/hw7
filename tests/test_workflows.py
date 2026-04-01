import asyncio

from trip_operator import workflows


def test_plan_trip_records_trace(monkeypatch):
    async def fake_call_tool(module_name, tool_name, arguments, trace=None):
        if trace is not None:
            trace.append({"server": module_name, "tool": tool_name, "payload": arguments})
        if tool_name == "build_trip_snapshot":
            return {
                "estimated_costs": {"total_usd": 500.0},
                "budget": {"travelers": 1, "daily_target_usd": 140.0},
                "assessment": {"within_budget": True},
                "cost_profile": {"tier": "standard"},
                "weather": {"available": True, "rain_risk_days": 0},
            }
        if tool_name == "create_trip_plan":
            return {"trip_id": "demo-trip", "budget_usd": 700.0, "start_date": "2026-04-03", "end_date": "2026-04-07"}
        if tool_name == "build_trip_calendar":
            assert arguments["planning_snapshot"]["estimated_costs"]["total_usd"] == 500.0
            assert arguments["travelers"] == 1
            assert arguments["notes"] == ""
            return {"calendar_path": "/tmp/demo-trip.ics"}
        if tool_name == "attach_calendar_path":
            return {"trip_id": "demo-trip", "calendar_path": "/tmp/demo-trip.ics"}
        raise AssertionError(f"Unexpected tool {tool_name}")

    monkeypatch.setattr(workflows, "call_tool", fake_call_tool)

    trace = []
    result = asyncio.run(
        workflows.plan_trip(
            destination="Las Vegas",
            start_date="2026-04-03",
            end_date="2026-04-07",
            budget_usd=700.0,
            home_city="Boise",
            travelers=1,
            trace=trace,
        )
    )

    assert result["trip"]["trip_id"] == "demo-trip"
    assert [entry["tool"] for entry in trace] == [
        "build_trip_snapshot",
        "create_trip_plan",
        "build_trip_calendar",
        "attach_calendar_path",
    ]


def test_get_trip_status_passes_snapshot_to_calendar_preview(monkeypatch):
    snapshot = {
        "budget": {"travelers": 2, "daily_target_usd": 180.0},
        "assessment": {"within_budget": True},
        "cost_profile": {"tier": "standard"},
        "weather": {"available": True, "rain_risk_days": 1},
    }

    async def fake_call_tool(module_name, tool_name, arguments, trace=None):
        if tool_name == "get_trip_budget_status":
            return {
                "trip": {
                    "trip_id": "demo-trip",
                    "destination": "Las Vegas",
                    "start_date": "2026-04-03",
                    "end_date": "2026-04-07",
                    "budget_usd": 900.0,
                    "travelers": 2,
                    "notes": "Focus on food.",
                    "metadata": snapshot,
                }
            }
        if tool_name == "get_trip_weather":
            return {"weather": {"summary": "Dry and warm."}}
        if tool_name == "preview_trip_calendar":
            assert arguments["planning_snapshot"] == snapshot
            assert arguments["travelers"] == 2
            assert arguments["notes"] == "Focus on food."
            return {"events": [], "daily_plan": []}
        raise AssertionError(f"Unexpected tool {tool_name}")

    monkeypatch.setattr(workflows, "call_tool", fake_call_tool)

    result = asyncio.run(workflows.get_trip_status("demo-trip"))

    assert result["reminders"] == {"events": [], "daily_plan": []}
