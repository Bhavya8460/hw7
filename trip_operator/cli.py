from __future__ import annotations

import argparse
import asyncio
from typing import Any

from trip_operator.workflows import (
    add_trip_expense,
    get_trip_status,
    import_trip_expenses,
    list_saved_trips,
    plan_trip,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trip Budget Operator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Create a new trip plan")
    plan_parser.add_argument("--destination", required=True)
    plan_parser.add_argument("--start", required=True, help="Trip start date in YYYY-MM-DD format")
    plan_parser.add_argument("--end", required=True, help="Trip end date in YYYY-MM-DD format")
    plan_parser.add_argument("--budget", required=True, type=float, help="Total trip budget in USD")
    plan_parser.add_argument("--home", default=None, help="Home city used for transport estimation")
    plan_parser.add_argument("--travelers", default=1, type=int)
    plan_parser.add_argument("--notes", default="")

    status_parser = subparsers.add_parser("status", help="Inspect a trip budget and reminder status")
    status_parser.add_argument("--trip-id", required=True)

    list_parser = subparsers.add_parser("list-trips", help="List saved trips")
    list_parser.set_defaults(command="list-trips")

    expense_parser = subparsers.add_parser("add-expense", help="Add one expense to a saved trip")
    expense_parser.add_argument("--trip-id", required=True)
    expense_parser.add_argument("--date", required=True, help="Expense date in YYYY-MM-DD format")
    expense_parser.add_argument("--category", required=True)
    expense_parser.add_argument("--amount", required=True, type=float)
    expense_parser.add_argument("--vendor", default="")
    expense_parser.add_argument("--notes", default="")

    import_parser = subparsers.add_parser("import-expenses", help="Import expenses from a CSV file")
    import_parser.add_argument("--trip-id", required=True)
    import_parser.add_argument("--csv", required=True)

    ui_parser = subparsers.add_parser("ui", help="Run the browser UI")
    ui_parser.add_argument("--host", default="127.0.0.1")
    ui_parser.add_argument("--port", default=8765, type=int)

    return parser


def render_trip_plan(snapshot: dict[str, Any], trip: dict[str, Any], calendar: dict[str, Any]) -> str:
    estimate = snapshot["estimated_costs"]
    weather = snapshot["weather"]
    lines = [
        f"Trip saved: {trip['trip_id']}",
        f"Destination: {snapshot['destination']['resolved_name']}",
        f"Dates: {trip['start_date']} to {trip['end_date']}",
        f"Budget: ${trip['budget_usd']:.2f}",
        f"Estimated total: ${estimate['total_usd']:.2f}",
        f"Budget gap: ${snapshot['assessment']['budget_gap_usd']:.2f}",
        f"Transport: ${estimate['transport_usd']:.2f} via {estimate['transport_details']['mode']}",
        f"Weather: {weather['summary']}",
        f"Calendar: {calendar['calendar_path']}",
        "Tips:",
    ]
    lines.extend(f"- {tip}" for tip in snapshot["tips"])
    daily_plan = calendar.get("daily_plan") or []
    if daily_plan:
        lines.append("Suggested day-by-day plan:")
        for day in daily_plan:
            lines.extend(
                [
                    f"- {day['date']}: {day['title']}",
                    f"  Morning: {day['morning']}",
                    f"  Afternoon: {day['afternoon']}",
                    f"  Evening: {day['evening']}",
                    f"  Spend cap: ${day['spend_target_usd']:.2f}",
                ]
            )
    return "\n".join(lines)


def render_list(trips: list[dict[str, Any]]) -> str:
    if not trips:
        return "No trips saved yet."
    lines = []
    for trip in trips:
        lines.append(
            f"{trip['trip_id']} | {trip['destination']} | {trip['start_date']} -> {trip['end_date']} | budget ${trip['budget_usd']:.2f}"
        )
    return "\n".join(lines)


def render_status(status: dict[str, Any], weather: dict[str, Any], reminders: dict[str, Any]) -> str:
    trip = status["trip"]
    reminder_lines = []
    for event in reminders["events"][:5]:
        reminder_lines.append(f"- {event['date']}: {event['title']}")

    plan_lines = []
    for day in (reminders.get("daily_plan") or [])[:3]:
        plan_lines.append(f"- {day['date']}: {day['title']} (cap ${day['spend_target_usd']:.2f})")

    category_lines = []
    for item in status["category_breakdown"][:5]:
        category_lines.append(f"- {item['category']}: ${item['total_usd']:.2f}")
    if not category_lines:
        category_lines.append("- No expenses recorded yet.")

    lines = [
        f"Trip: {trip['trip_id']}",
        f"Destination: {trip['destination']}",
        f"Budget: ${trip['budget_usd']:.2f}",
        f"Estimated plan total: ${trip['estimated_total_usd']:.2f}",
        f"Spent so far: ${status['spent_total_usd']:.2f}",
        f"Remaining budget: ${status['remaining_budget_usd']:.2f}",
        f"Spend pace delta: ${status['pace_delta_usd']:.2f}",
        f"Weather: {weather['weather']['summary']}",
        "Top categories:",
    ]
    lines.extend(category_lines)
    if plan_lines:
        lines.append("Suggested daily plan:")
        lines.extend(plan_lines)
    lines.append("Upcoming reminders:")
    lines.extend(reminder_lines)
    return "\n".join(lines)


async def run_plan(args: argparse.Namespace) -> str:
    result = await plan_trip(
        destination=args.destination,
        start_date=args.start,
        end_date=args.end,
        budget_usd=args.budget,
        home_city=args.home,
        travelers=args.travelers,
        notes=args.notes,
    )
    return render_trip_plan(result["snapshot"], result["trip"], result["calendar"])


async def run_status(args: argparse.Namespace) -> str:
    result = await get_trip_status(args.trip_id)
    return render_status(result["status"], result["weather"], result["reminders"])


async def run_list_trips(_: argparse.Namespace) -> str:
    trips = await list_saved_trips()
    return render_list(trips["trips"])


async def run_add_expense(args: argparse.Namespace) -> str:
    item = await add_trip_expense(
        trip_id=args.trip_id,
        expense_date=args.date,
        category=args.category,
        amount_usd=args.amount,
        vendor=args.vendor,
        notes=args.notes,
    )
    return f"Expense saved: #{item['id']} {item['category']} ${item['amount_usd']:.2f}"


async def run_import_expenses(args: argparse.Namespace) -> str:
    result = await import_trip_expenses(args.trip_id, args.csv)
    return f"Imported {result['imported_count']} expenses into {result['trip_id']}."


async def dispatch(args: argparse.Namespace) -> str:
    if args.command == "plan":
        return await run_plan(args)
    if args.command == "status":
        return await run_status(args)
    if args.command == "list-trips":
        return await run_list_trips(args)
    if args.command == "add-expense":
        return await run_add_expense(args)
    if args.command == "import-expenses":
        return await run_import_expenses(args)
    raise ValueError(f"Unknown command: {args.command}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "ui":
        from trip_operator.webapp import run_dev_server

        run_dev_server(args.host, args.port)
        return 0
    print(asyncio.run(dispatch(args)))
    return 0
