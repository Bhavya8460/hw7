from __future__ import annotations

import csv
import json
import re
import sqlite3
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from trip_operator.config import DB_PATH
from trip_operator.travel import parse_iso_date, trip_days_and_nights


def initialize_database(db_path: Path | str = DB_PATH) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                destination TEXT NOT NULL,
                home_city TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                travelers INTEGER NOT NULL,
                budget_usd REAL NOT NULL,
                estimated_total_usd REAL NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                calendar_path TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount_usd REAL NOT NULL,
                vendor TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(trip_id) REFERENCES trips(trip_id)
            )
            """
        )


def _connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "trip"


def _trip_row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
    return item


def create_trip_plan(
    destination: str,
    home_city: str | None,
    start_date: str,
    end_date: str,
    budget_usd: float,
    travelers: int,
    planning_snapshot: dict[str, Any],
    notes: str = "",
    db_path: Path | str = DB_PATH,
) -> dict[str, Any]:
    initialize_database(db_path)
    trip_days_and_nights(start_date, end_date)
    trip_id = f"{_slugify(destination)}-{start_date.replace('-', '')}-{uuid.uuid4().hex[:6]}"
    estimated_total = float(planning_snapshot["estimated_costs"]["total_usd"])
    created_at = datetime.now(UTC).isoformat(timespec="seconds")

    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO trips (
                trip_id, destination, home_city, start_date, end_date, travelers,
                budget_usd, estimated_total_usd, notes, calendar_path, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trip_id,
                destination,
                home_city,
                start_date,
                end_date,
                travelers,
                float(budget_usd),
                estimated_total,
                notes,
                None,
                json.dumps(planning_snapshot, sort_keys=True),
                created_at,
            ),
        )

    trip = get_trip(trip_id, db_path=db_path)
    if trip is None:
        raise RuntimeError("Trip was not saved correctly.")
    return trip


def get_trip(trip_id: str, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    initialize_database(db_path)
    with _connect(db_path) as connection:
        row = connection.execute("SELECT * FROM trips WHERE trip_id = ?", (trip_id,)).fetchone()
    return _trip_row_to_dict(row)


def list_trips(db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with _connect(db_path) as connection:
        rows = connection.execute("SELECT * FROM trips ORDER BY created_at DESC").fetchall()
    return [_trip_row_to_dict(row) for row in rows]


def set_calendar_path(trip_id: str, calendar_path: str, db_path: Path | str = DB_PATH) -> dict[str, Any]:
    initialize_database(db_path)
    with _connect(db_path) as connection:
        updated = connection.execute(
            "UPDATE trips SET calendar_path = ? WHERE trip_id = ?",
            (calendar_path, trip_id),
        )
        if updated.rowcount == 0:
            raise ValueError(f"Trip {trip_id!r} does not exist.")
    trip = get_trip(trip_id, db_path=db_path)
    if trip is None:
        raise RuntimeError("Trip path update failed.")
    return trip


def add_expense(
    trip_id: str,
    expense_date: str,
    category: str,
    amount_usd: float,
    vendor: str = "",
    notes: str = "",
    db_path: Path | str = DB_PATH,
) -> dict[str, Any]:
    initialize_database(db_path)
    if get_trip(trip_id, db_path=db_path) is None:
        raise ValueError(f"Trip {trip_id!r} does not exist.")
    parse_iso_date(expense_date)

    item = {
        "trip_id": trip_id,
        "expense_date": expense_date,
        "category": category.strip().lower(),
        "amount_usd": round(float(amount_usd), 2),
        "vendor": vendor.strip(),
        "notes": notes.strip(),
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO expenses (trip_id, expense_date, category, amount_usd, vendor, notes, created_at)
            VALUES (:trip_id, :expense_date, :category, :amount_usd, :vendor, :notes, :created_at)
            """,
            item,
        )
        item["id"] = cursor.lastrowid
    return item


def import_expenses_from_csv(trip_id: str, csv_path: str, db_path: Path | str = DB_PATH) -> dict[str, Any]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Expense CSV not found: {csv_path}")

    imported = 0
    imported_rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            expense_date = row.get("date") or row.get("expense_date")
            amount = row.get("amount") or row.get("amount_usd")
            category = row.get("category")
            if not expense_date or not amount or not category:
                raise ValueError("CSV rows must include date, category, and amount.")
            imported_rows.append(
                add_expense(
                    trip_id=trip_id,
                    expense_date=expense_date,
                    category=category,
                    amount_usd=float(amount),
                    vendor=row.get("vendor", ""),
                    notes=row.get("notes", ""),
                    db_path=db_path,
                )
            )
            imported += 1

    return {"trip_id": trip_id, "imported_count": imported, "items": imported_rows}


def get_budget_status(trip_id: str, db_path: Path | str = DB_PATH) -> dict[str, Any]:
    trip = get_trip(trip_id, db_path=db_path)
    if trip is None:
        raise ValueError(f"Trip {trip_id!r} does not exist.")

    with _connect(db_path) as connection:
        expense_rows = connection.execute(
            "SELECT * FROM expenses WHERE trip_id = ? ORDER BY expense_date, id",
            (trip_id,),
        ).fetchall()
        category_rows = connection.execute(
            """
            SELECT category, ROUND(SUM(amount_usd), 2) AS total_usd
            FROM expenses
            WHERE trip_id = ?
            GROUP BY category
            ORDER BY total_usd DESC
            """,
            (trip_id,),
        ).fetchall()

    expenses = [dict(row) for row in expense_rows]
    spent_total = round(sum(item["amount_usd"] for item in expenses), 2)
    remaining_budget = round(trip["budget_usd"] - spent_total, 2)
    days_total, _ = trip_days_and_nights(trip["start_date"], trip["end_date"])

    today = date.today()
    start = parse_iso_date(trip["start_date"])
    end = parse_iso_date(trip["end_date"])
    if today < start:
        elapsed_days = 0
    elif today > end:
        elapsed_days = days_total
    else:
        elapsed_days = (today - start).days + 1

    expected_spend_to_date = round((trip["budget_usd"] / max(days_total, 1)) * elapsed_days, 2)
    pace_delta = round(spent_total - expected_spend_to_date, 2)

    return {
        "trip": trip,
        "expenses": expenses,
        "expense_count": len(expenses),
        "spent_total_usd": spent_total,
        "remaining_budget_usd": remaining_budget,
        "budget_vs_estimate_usd": round(trip["budget_usd"] - trip["estimated_total_usd"], 2),
        "expected_spend_to_date_usd": expected_spend_to_date,
        "pace_delta_usd": pace_delta,
        "on_track": remaining_budget >= 0,
        "category_breakdown": [dict(row) for row in category_rows],
    }
