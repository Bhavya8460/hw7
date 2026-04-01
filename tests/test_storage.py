from trip_operator.storage import add_expense, create_trip_plan, get_budget_status


def test_budget_status_rolls_up_expenses(tmp_path):
    db_path = tmp_path / "trips.db"
    snapshot = {
        "estimated_costs": {"total_usd": 620.0},
        "assessment": {"budget_gap_usd": 80.0},
    }
    trip = create_trip_plan(
        destination="Las Vegas",
        home_city="Boise",
        start_date="2026-04-03",
        end_date="2026-04-07",
        budget_usd=700.0,
        travelers=1,
        planning_snapshot=snapshot,
        db_path=db_path,
    )
    add_expense(trip["trip_id"], "2026-04-03", "food", 21.5, db_path=db_path)
    add_expense(trip["trip_id"], "2026-04-03", "transport", 14.0, db_path=db_path)

    status = get_budget_status(trip["trip_id"], db_path=db_path)

    assert status["spent_total_usd"] == 35.5
    assert status["remaining_budget_usd"] == 664.5
    assert len(status["category_breakdown"]) == 2

