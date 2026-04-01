from __future__ import annotations

import asyncio
from datetime import date, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Any

import httpx

USER_AGENT = "TripBudgetOperator/0.1 (student project)"

FALLBACK_LOCATIONS: dict[str, dict[str, Any]] = {
    "bangkok": {"display_name": "Bangkok, Thailand", "latitude": 13.7563, "longitude": 100.5018, "country_code": "TH"},
    "boise": {"display_name": "Boise, Idaho, United States", "latitude": 43.6150, "longitude": -116.2023, "country_code": "US"},
    "chicago": {"display_name": "Chicago, Illinois, United States", "latitude": 41.8781, "longitude": -87.6298, "country_code": "US"},
    "las vegas": {"display_name": "Las Vegas, Nevada, United States", "latitude": 36.1699, "longitude": -115.1398, "country_code": "US"},
    "london": {"display_name": "London, United Kingdom", "latitude": 51.5072, "longitude": -0.1276, "country_code": "GB"},
    "los angeles": {"display_name": "Los Angeles, California, United States", "latitude": 34.0522, "longitude": -118.2437, "country_code": "US"},
    "mexico city": {"display_name": "Mexico City, Mexico", "latitude": 19.4326, "longitude": -99.1332, "country_code": "MX"},
    "miami": {"display_name": "Miami, Florida, United States", "latitude": 25.7617, "longitude": -80.1918, "country_code": "US"},
    "new york": {"display_name": "New York, New York, United States", "latitude": 40.7128, "longitude": -74.0060, "country_code": "US"},
    "paris": {"display_name": "Paris, France", "latitude": 48.8566, "longitude": 2.3522, "country_code": "FR"},
    "san francisco": {"display_name": "San Francisco, California, United States", "latitude": 37.7749, "longitude": -122.4194, "country_code": "US"},
    "tokyo": {"display_name": "Tokyo, Japan", "latitude": 35.6764, "longitude": 139.6500, "country_code": "JP"},
}

CITY_PROFILES: dict[str, dict[str, Any]] = {
    "bangkok": {"city": "Bangkok", "currency_code": "THB", "tier": "value", "hotel_mid": 58.0, "food_per_day": 26.0, "transit_per_day": 9.0, "activity_per_day": 25.0},
    "chicago": {"city": "Chicago", "currency_code": "USD", "tier": "standard", "hotel_mid": 165.0, "food_per_day": 65.0, "transit_per_day": 20.0, "activity_per_day": 55.0},
    "las vegas": {"city": "Las Vegas", "currency_code": "USD", "tier": "standard", "hotel_mid": 108.0, "food_per_day": 52.0, "transit_per_day": 18.0, "activity_per_day": 40.0},
    "london": {"city": "London", "currency_code": "GBP", "tier": "premium", "hotel_mid": 195.0, "food_per_day": 80.0, "transit_per_day": 24.0, "activity_per_day": 70.0},
    "los angeles": {"city": "Los Angeles", "currency_code": "USD", "tier": "premium", "hotel_mid": 205.0, "food_per_day": 72.0, "transit_per_day": 28.0, "activity_per_day": 65.0},
    "mexico city": {"city": "Mexico City", "currency_code": "MXN", "tier": "value", "hotel_mid": 70.0, "food_per_day": 30.0, "transit_per_day": 10.0, "activity_per_day": 28.0},
    "miami": {"city": "Miami", "currency_code": "USD", "tier": "premium", "hotel_mid": 198.0, "food_per_day": 75.0, "transit_per_day": 24.0, "activity_per_day": 58.0},
    "new york": {"city": "New York", "currency_code": "USD", "tier": "premium", "hotel_mid": 245.0, "food_per_day": 78.0, "transit_per_day": 24.0, "activity_per_day": 72.0},
    "paris": {"city": "Paris", "currency_code": "EUR", "tier": "premium", "hotel_mid": 185.0, "food_per_day": 74.0, "transit_per_day": 19.0, "activity_per_day": 60.0},
    "san francisco": {"city": "San Francisco", "currency_code": "USD", "tier": "premium", "hotel_mid": 225.0, "food_per_day": 76.0, "transit_per_day": 26.0, "activity_per_day": 64.0},
    "tokyo": {"city": "Tokyo", "currency_code": "JPY", "tier": "standard", "hotel_mid": 132.0, "food_per_day": 48.0, "transit_per_day": 16.0, "activity_per_day": 42.0},
}

COUNTRY_DEFAULTS: dict[str, dict[str, Any]] = {
    "FR": {"currency_code": "EUR", "tier": "premium", "hotel_mid": 170.0, "food_per_day": 68.0, "transit_per_day": 18.0, "activity_per_day": 55.0},
    "GB": {"currency_code": "GBP", "tier": "premium", "hotel_mid": 180.0, "food_per_day": 72.0, "transit_per_day": 20.0, "activity_per_day": 60.0},
    "JP": {"currency_code": "JPY", "tier": "standard", "hotel_mid": 125.0, "food_per_day": 46.0, "transit_per_day": 15.0, "activity_per_day": 40.0},
    "MX": {"currency_code": "MXN", "tier": "value", "hotel_mid": 75.0, "food_per_day": 28.0, "transit_per_day": 10.0, "activity_per_day": 26.0},
    "TH": {"currency_code": "THB", "tier": "value", "hotel_mid": 55.0, "food_per_day": 24.0, "transit_per_day": 9.0, "activity_per_day": 24.0},
    "US": {"currency_code": "USD", "tier": "standard", "hotel_mid": 150.0, "food_per_day": 58.0, "transit_per_day": 18.0, "activity_per_day": 42.0},
}

GENERIC_PROFILE = {
    "currency_code": "USD",
    "tier": "standard",
    "hotel_mid": 145.0,
    "food_per_day": 55.0,
    "transit_per_day": 18.0,
    "activity_per_day": 38.0,
}

WEATHER_CODES = {
    0: "clear",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    51: "light drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    71: "snow",
    80: "showers",
    95: "thunderstorms",
}


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def trip_days_and_nights(start_date: str, end_date: str) -> tuple[int, int]:
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    nights = (end - start).days
    days = nights + 1
    return days, nights


def normalize_city_key(value: str) -> str:
    return " ".join(value.strip().lower().split())


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    a = sin(d_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


async def geocode_place(query: str) -> dict[str, Any]:
    normalized = normalize_city_key(query)
    fallback = FALLBACK_LOCATIONS.get(normalized)

    params = {"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1}
    headers = {"User-Agent": USER_AGENT}
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.get("https://nominatim.openstreetmap.org/search", params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        if fallback:
            return {**fallback, "source": "fallback", "warning": f"geocoder fallback used: {exc}"}
        raise RuntimeError(f"Could not geocode {query!r}: {exc}") from exc

    if payload:
        item = payload[0]
        return {
            "display_name": item.get("display_name", query),
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
            "country_code": item.get("address", {}).get("country_code", "").upper() or (fallback or {}).get("country_code", "US"),
            "source": "nominatim",
        }

    if fallback:
        return {**fallback, "source": "fallback", "warning": "No geocoder match found; using local fallback."}
    raise ValueError(f"No location match found for {query!r}")


def get_cost_profile(destination: str, country_code: str | None = None) -> dict[str, Any]:
    normalized = normalize_city_key(destination)
    if normalized in CITY_PROFILES:
        return {**CITY_PROFILES[normalized], "profile_source": "city"}
    if country_code and country_code in COUNTRY_DEFAULTS:
        return {**COUNTRY_DEFAULTS[country_code], "city": destination, "profile_source": "country"}
    return {**GENERIC_PROFILE, "city": destination, "profile_source": "generic"}


async def fetch_exchange_rate(currency_code: str) -> dict[str, Any]:
    if currency_code == "USD":
        return {"currency_code": "USD", "usd_to_local": 1.0, "source": "identity"}

    params = {"from": "USD", "to": currency_code}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.frankfurter.app/latest", params=params)
            response.raise_for_status()
            payload = response.json()
        rate = float(payload["rates"][currency_code])
        return {"currency_code": currency_code, "usd_to_local": rate, "source": "frankfurter"}
    except Exception as exc:
        return {"currency_code": currency_code, "usd_to_local": None, "source": "unavailable", "warning": f"Exchange rate unavailable: {exc}"}


async def fetch_weather_summary(latitude: float, longitude: float, start_date: str, end_date: str) -> dict[str, Any]:
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)
    today = date.today()
    if start < today or end > today + timedelta(days=15):
        return {
            "available": False,
            "summary": "Open-Meteo forecast is only reliable for roughly the next 16 days.",
            "source": "open-meteo",
        }

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {"available": False, "summary": f"Weather unavailable: {exc}", "source": "open-meteo"}

    daily = payload.get("daily", {})
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    rain_probs = daily.get("precipitation_probability_max", [])
    weather_codes = daily.get("weather_code", [])

    if not max_temps:
        return {"available": False, "summary": "Weather data returned empty.", "source": "open-meteo"}

    avg_high = round(sum(max_temps) / len(max_temps), 1)
    avg_low = round(sum(min_temps) / len(min_temps), 1)
    rainy_days = sum(1 for value in rain_probs if value >= 40)
    dominant_code = weather_codes[0] if weather_codes else None
    description = WEATHER_CODES.get(dominant_code, "mixed conditions")

    return {
        "available": True,
        "summary": f"{description.capitalize()} with average highs near {avg_high}C and lows near {avg_low}C.",
        "average_high_c": avg_high,
        "average_low_c": avg_low,
        "rain_risk_days": rainy_days,
        "source": "open-meteo",
    }


def estimate_transport_cost(home_location: dict[str, Any] | None, destination_location: dict[str, Any], travelers: int) -> dict[str, Any]:
    if not home_location:
        fallback_total = round(180.0 * max(travelers, 1), 2)
        return {
            "mode": "generic transport assumption",
            "distance_km": None,
            "total_usd": fallback_total,
            "notes": "No home city provided, so transport uses a generic low-cost estimate.",
        }

    distance_km = haversine_km(
        home_location["latitude"],
        home_location["longitude"],
        destination_location["latitude"],
        destination_location["longitude"],
    )
    if distance_km < 350:
        mode = "car or bus"
        total = 45.0 + (distance_km * 0.16)
    elif distance_km < 1200:
        mode = "budget flight"
        total = 95.0 + (distance_km * 0.10)
    elif distance_km < 3500:
        mode = "economy flight"
        total = 160.0 + (distance_km * 0.08)
    else:
        mode = "long-haul economy flight"
        total = 280.0 + (distance_km * 0.07)

    total *= max(travelers, 1)
    return {
        "mode": mode,
        "distance_km": round(distance_km, 1),
        "total_usd": round(total, 2),
        "notes": f"Estimated from straight-line distance between {home_location['display_name']} and {destination_location['display_name']}.",
    }


def build_cost_saving_tips(
    days: int,
    budget_usd: float,
    total_estimate_usd: float,
    transport: dict[str, Any],
    weather: dict[str, Any],
    profile: dict[str, Any],
) -> list[str]:
    tips: list[str] = []
    daily_target = round(budget_usd / max(days, 1), 2)
    expected_daily = round(total_estimate_usd / max(days, 1), 2)

    if total_estimate_usd > budget_usd:
        tips.append(f"The current plan is ${round(total_estimate_usd - budget_usd, 2):.2f} over budget. Reduce hotel nights, activities, or transport first.")
    else:
        tips.append(f"Your projected spend is ${round(budget_usd - total_estimate_usd, 2):.2f} under budget, leaving room for a buffer or one premium activity.")

    if transport["total_usd"] > budget_usd * 0.35:
        tips.append("Transport is taking a large share of the budget. Compare nearby airports or shift departure times.")

    if profile["tier"] == "premium":
        tips.append("The destination has a premium cost profile. Book lodging early and avoid last-minute meals near tourist zones.")
    elif profile["tier"] == "value":
        tips.append("This destination is relatively budget-friendly, so keep the savings by capping activities before upgrading hotels.")

    if weather.get("available") and weather.get("rain_risk_days", 0) >= 2:
        tips.append("Rain risk is meaningful during the trip window. Prioritize indoor backup activities to avoid wasted spend.")

    tips.append(f"Target an average daily spend of about ${daily_target:.2f}. The current estimate is ${expected_daily:.2f} per day.")
    return tips


async def get_trip_weather(destination: str, start_date: str, end_date: str) -> dict[str, Any]:
    location = await geocode_place(destination)
    weather = await fetch_weather_summary(location["latitude"], location["longitude"], start_date, end_date)
    return {"destination": location["display_name"], "weather": weather}


async def build_trip_snapshot(
    destination: str,
    start_date: str,
    end_date: str,
    budget_usd: float,
    home_city: str | None = None,
    travelers: int = 1,
) -> dict[str, Any]:
    days, nights = trip_days_and_nights(start_date, end_date)

    destination_task = asyncio.create_task(geocode_place(destination))
    home_task = asyncio.create_task(geocode_place(home_city)) if home_city else None

    destination_location = await destination_task
    home_location = await home_task if home_task else None
    profile = get_cost_profile(destination, destination_location.get("country_code"))

    weather_task = asyncio.create_task(
        fetch_weather_summary(destination_location["latitude"], destination_location["longitude"], start_date, end_date)
    )
    exchange_task = asyncio.create_task(fetch_exchange_rate(profile["currency_code"]))

    transport = estimate_transport_cost(home_location, destination_location, travelers)
    lodging = round(nights * profile["hotel_mid"], 2)
    food = round(days * profile["food_per_day"] * travelers, 2)
    local_transit = round(days * profile["transit_per_day"] * travelers, 2)
    activities = round(days * profile["activity_per_day"] * travelers, 2)
    total_estimate = round(transport["total_usd"] + lodging + food + local_transit + activities, 2)

    weather, exchange_rate = await asyncio.gather(weather_task, exchange_task)
    converted_total = None
    if exchange_rate.get("usd_to_local"):
        converted_total = round(total_estimate * exchange_rate["usd_to_local"], 2)

    return {
        "destination": {
            "requested": destination,
            "resolved_name": destination_location["display_name"],
            "country_code": destination_location.get("country_code", "US"),
            "latitude": destination_location["latitude"],
            "longitude": destination_location["longitude"],
            "source": destination_location.get("source"),
        },
        "home_city": home_location,
        "dates": {
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "nights": nights,
        },
        "budget": {
            "limit_usd": round(float(budget_usd), 2),
            "daily_target_usd": round(float(budget_usd) / max(days, 1), 2),
            "travelers": travelers,
        },
        "cost_profile": {
            "tier": profile["tier"],
            "currency_code": profile["currency_code"],
            "profile_source": profile["profile_source"],
        },
        "weather": weather,
        "estimated_costs": {
            "transport_usd": transport["total_usd"],
            "lodging_usd": lodging,
            "food_usd": food,
            "local_transport_usd": local_transit,
            "activities_usd": activities,
            "total_usd": total_estimate,
            "transport_details": transport,
            "destination_currency_code": exchange_rate["currency_code"],
            "total_in_destination_currency": converted_total,
        },
        "assessment": {
            "within_budget": total_estimate <= budget_usd,
            "budget_gap_usd": round(float(budget_usd) - total_estimate, 2),
            "recommended_budget_usd": round(total_estimate * 1.10, 2),
        },
        "tips": build_cost_saving_tips(days, float(budget_usd), total_estimate, transport, weather, profile),
        "service_sources": {
            "geocoding": destination_location.get("source"),
            "weather": weather.get("source"),
            "exchange_rate": exchange_rate.get("source"),
        },
    }


def supported_destinations() -> list[str]:
    return sorted(profile["city"] for profile in CITY_PROFILES.values())

