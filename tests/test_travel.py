import asyncio

from trip_operator import travel


def test_build_trip_snapshot_with_monkeypatched_services(monkeypatch):
    async def fake_geocode(value: str):
        locations = {
            "Las Vegas": {"display_name": "Las Vegas, Nevada, United States", "latitude": 36.1699, "longitude": -115.1398, "country_code": "US", "source": "fake"},
            "Boise": {"display_name": "Boise, Idaho, United States", "latitude": 43.6150, "longitude": -116.2023, "country_code": "US", "source": "fake"},
        }
        return locations[value]

    async def fake_weather(latitude: float, longitude: float, start_date: str, end_date: str):
        return {"available": True, "summary": "Dry and warm.", "rain_risk_days": 0, "source": "fake"}

    async def fake_rate(currency_code: str):
        return {"currency_code": currency_code, "usd_to_local": 1.0, "source": "fake"}

    monkeypatch.setattr(travel, "geocode_place", fake_geocode)
    monkeypatch.setattr(travel, "fetch_weather_summary", fake_weather)
    monkeypatch.setattr(travel, "fetch_exchange_rate", fake_rate)

    snapshot = asyncio.run(
        travel.build_trip_snapshot(
            destination="Las Vegas",
            start_date="2026-04-03",
            end_date="2026-04-07",
            budget_usd=700.0,
            home_city="Boise",
            travelers=1,
        )
    )

    assert snapshot["destination"]["resolved_name"].startswith("Las Vegas")
    assert snapshot["weather"]["summary"] == "Dry and warm."
    assert snapshot["estimated_costs"]["total_usd"] > 0
    assert snapshot["assessment"]["recommended_budget_usd"] >= snapshot["estimated_costs"]["total_usd"]
