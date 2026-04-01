from __future__ import annotations

from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

from trip_operator.config import ROOT_DIR
from trip_operator.reporting import XLSX_MEDIA_TYPE, build_trip_report_filename, build_trip_report_workbook
from trip_operator.workflows import add_trip_expense, get_trip_status, list_saved_trips, plan_trip

WEB_DIR = ROOT_DIR / "trip_operator" / "web"
NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _error_response(exc: Exception, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"ok": False, "error": str(exc)}, status_code=status_code)


async def index(_: Request):
    return FileResponse(WEB_DIR / "index.html", headers=NO_CACHE_HEADERS)


async def app_js(_: Request):
    return FileResponse(WEB_DIR / "app.js", media_type="application/javascript", headers=NO_CACHE_HEADERS)


async def styles_css(_: Request):
    return FileResponse(WEB_DIR / "styles.css", media_type="text/css", headers=NO_CACHE_HEADERS)


async def api_plan(request: Request):
    try:
        body = await request.json()
        trace: list[dict] = []
        result = await plan_trip(
            destination=body["destination"],
            start_date=body["start_date"],
            end_date=body["end_date"],
            budget_usd=float(body["budget_usd"]),
            home_city=body.get("home_city") or None,
            travelers=int(body.get("travelers", 1)),
            notes=body.get("notes", ""),
            trace=trace,
        )
        return JSONResponse({"ok": True, "result": result, "trace": trace})
    except Exception as exc:
        return _error_response(exc)


async def api_trips(_: Request):
    try:
        trace: list[dict] = []
        result = await list_saved_trips(trace=trace)
        return JSONResponse({"ok": True, "result": result, "trace": trace})
    except Exception as exc:
        return _error_response(exc)


async def api_status(request: Request):
    trip_id = request.query_params.get("trip_id")
    if not trip_id:
        return _error_response(ValueError("trip_id is required"))
    try:
        trace: list[dict] = []
        result = await get_trip_status(trip_id, trace=trace)
        return JSONResponse({"ok": True, "result": result, "trace": trace})
    except Exception as exc:
        return _error_response(exc)


async def api_expense(request: Request):
    try:
        body = await request.json()
        trace: list[dict] = []
        result = await add_trip_expense(
            trip_id=body["trip_id"],
            expense_date=body["expense_date"],
            category=body["category"],
            amount_usd=float(body["amount_usd"]),
            vendor=body.get("vendor", ""),
            notes=body.get("notes", ""),
            trace=trace,
        )
        return JSONResponse({"ok": True, "result": result, "trace": trace})
    except Exception as exc:
        return _error_response(exc)


async def api_export(request: Request):
    trip_id = request.query_params.get("trip_id")
    if not trip_id:
        return _error_response(ValueError("trip_id is required"))
    try:
        result = await get_trip_status(trip_id)
        workbook = build_trip_report_workbook(result)
        headers = {
            "Content-Disposition": f'attachment; filename="{build_trip_report_filename(trip_id)}"',
        }
        return Response(workbook, media_type=XLSX_MEDIA_TYPE, headers=headers)
    except Exception as exc:
        return _error_response(exc)


app = Starlette(
    debug=True,
    routes=[
        Route("/", index),
        Route("/app.js", app_js),
        Route("/styles.css", styles_css),
        Route("/api/plan", api_plan, methods=["POST"]),
        Route("/api/trips", api_trips),
        Route("/api/status", api_status),
        Route("/api/expense", api_expense, methods=["POST"]),
        Route("/api/export", api_export),
    ],
)


def run_dev_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    run_dev_server()
