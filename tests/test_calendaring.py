from trip_operator.calendaring import build_trip_calendar, build_trip_events, preview_trip_calendar


def test_calendar_export_creates_ics(tmp_path):
    events = build_trip_events("Las Vegas", "2026-04-03", "2026-04-05", 450.0)
    assert len(events) >= 6

    result = build_trip_calendar(
        trip_id="demo-trip",
        destination="Las Vegas",
        start_date="2026-04-03",
        end_date="2026-04-05",
        budget_usd=450.0,
        output_path=tmp_path / "demo.ics",
    )

    assert result["calendar_path"].endswith("demo.ics")
    assert len(result["daily_plan"]) == 3
    content = (tmp_path / "demo.ics").read_text(encoding="utf-8")
    assert "BEGIN:VCALENDAR" in content
    assert "Daily spend check" in content
    assert "Day 1 plan:" in content


def test_calendar_preview_includes_daily_plan_details():
    snapshot = {
        "budget": {"daily_target_usd": 140.0, "travelers": 1},
        "assessment": {"within_budget": True},
        "cost_profile": {"tier": "standard"},
        "weather": {"available": True, "rain_risk_days": 0},
    }

    preview = preview_trip_calendar(
        destination="Las Vegas",
        start_date="2026-04-03",
        end_date="2026-04-06",
        budget_usd=560.0,
        planning_snapshot=snapshot,
        notes="Prioritize food markets and cafe stops.",
    )

    assert len(preview["daily_plan"]) == 4
    assert preview["daily_plan"][1]["theme"] == "Food crawl and market stops"
    assert any(event["kind"] == "itinerary" for event in preview["events"])
