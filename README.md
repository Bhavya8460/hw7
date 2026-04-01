# Trip Budget Operator

Trip Budget Operator is a practical MCP application for a real problem: planning a trip without blowing the budget or missing logistics. It uses three MCP servers and live external services where they add value without requiring API keys.

## What it solves

Planning a cheap trip usually means switching between weather sites, budget spreadsheets, reminders, and scattered notes. This app turns that into one workflow:

- builds a live trip snapshot with destination geocoding, weather, and currency conversion
- stores a budget plan and tracks real expenses
- generates a calendar file with booking reminders, daily spend checks, and a suggested day-by-day activity plan

## The 3 MCP servers

1. `travel_mcp`
   - geocodes the destination and home city
   - pulls a live weather forecast from Open-Meteo when the trip is within the forecast window
   - estimates transport, lodging, food, local transit, and activity costs
   - converts the estimate into the destination currency

2. `budget_mcp`
   - saves trips in SQLite
   - records expenses or imports them from CSV
   - reports whether the trip is still on budget

3. `calendar_mcp`
   - creates reminder events for the trip
   - builds a suggested itinerary for each trip day from the budget, weather, cost tier, and notes
   - exports a standard `.ics` calendar file you can import into Google Calendar, Apple Calendar, or Outlook

## External services used

- Nominatim / OpenStreetMap for destination lookup
- Open-Meteo for live weather
- Frankfurter for exchange rates

If those services fail, the app degrades gracefully with local fallbacks.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -e .
```

## Usage

Run the browser UI:

```bash
./.venv/bin/python main.py ui
```

Then open `http://127.0.0.1:8765`.

The UI is the easiest place to give input:

- the left panel is where you enter trip details, load an existing trip, or add an expense
- the right panel shows the result, including the day-by-day plan, the raw JSON response, and an MCP trace for every tool call
- the trace shows the orchestration path:
  `Browser UI -> web app -> MCP client -> travel_mcp / budget_mcp / calendar_mcp`

Create a plan:

```bash
./.venv/bin/python main.py plan \
  --destination "Las Vegas" \
  --start 2026-04-03 \
  --end 2026-04-07 \
  --budget 700 \
  --home "Boise"
```

List saved trips:

```bash
./.venv/bin/python main.py list-trips
```

Check status:

```bash
./.venv/bin/python main.py status --trip-id las-vegas-20260403-abc123
```

Add an expense:

```bash
./.venv/bin/python main.py add-expense \
  --trip-id las-vegas-20260403-abc123 \
  --date 2026-04-04 \
  --category food \
  --amount 28.50 \
  --vendor "Ellis Island Cafe"
```

Import expenses from CSV:

```bash
./.venv/bin/python main.py import-expenses \
  --trip-id las-vegas-20260403-abc123 \
  --csv expenses.csv
```

Expected CSV columns:

- `date` or `expense_date`
- `category`
- `amount` or `amount_usd`
- optional: `vendor`
- optional: `notes`

## Architecture

- [main.py](/Users/bhavya/Desktop/Sem 4/AI in Business/hw7/main.py) is the CLI entrypoint
- [trip_operator/cli.py](/Users/bhavya/Desktop/Sem 4/AI in Business/hw7/trip_operator/cli.py) is the MCP client orchestrator
- [trip_operator/webapp.py](/Users/bhavya/Desktop/Sem 4/AI in Business/hw7/trip_operator/webapp.py) serves the browser UI and JSON API
- [trip_operator/workflows.py](/Users/bhavya/Desktop/Sem 4/AI in Business/hw7/trip_operator/workflows.py) defines the cross-server MCP workflow steps
- [mcp_servers/travel_server.py](/Users/bhavya/Desktop/Sem 4/AI in Business/hw7/mcp_servers/travel_server.py) exposes travel planning tools
- [mcp_servers/budget_server.py](/Users/bhavya/Desktop/Sem 4/AI in Business/hw7/mcp_servers/budget_server.py) exposes budget storage tools
- [mcp_servers/calendar_server.py](/Users/bhavya/Desktop/Sem 4/AI in Business/hw7/mcp_servers/calendar_server.py) exposes reminder and calendar tools

## How the MCP pieces talk

The MCP servers do not call each other directly. The client orchestrates them in sequence:

1. `travel_mcp.build_trip_snapshot`
2. `budget_mcp.create_trip_plan`
3. `calendar_mcp.build_trip_calendar`
4. `budget_mcp.attach_calendar_path`

For status checks the sequence is:

1. `budget_mcp.get_trip_budget_status`
2. `travel_mcp.get_trip_weather`
3. `calendar_mcp.preview_trip_calendar`

The UI trace panel shows those calls as client-to-server and server-to-client events over MCP `stdio` transport.
