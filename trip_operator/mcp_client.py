from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from trip_operator.config import ROOT_DIR


def server_python() -> str:
    venv_python = ROOT_DIR / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


@asynccontextmanager
async def open_mcp_session(module_name: str):
    env = dict(os.environ)
    current_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(ROOT_DIR) if not current_pythonpath else f"{ROOT_DIR}:{current_pythonpath}"
    params = StdioServerParameters(
        command=server_python(),
        args=["-m", module_name],
        cwd=ROOT_DIR,
        env=env,
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


def _extract_tool_payload(result: Any) -> Any:
    if getattr(result, "structuredContent", None) is not None:
        return result.structuredContent

    text_fragments: list[str] = []
    for item in getattr(result, "content", []):
        if isinstance(item, TextContent):
            text_fragments.append(item.text)

    if not text_fragments:
        return result.model_dump(mode="json")

    combined = "\n".join(text_fragments)
    try:
        return json.loads(combined)
    except json.JSONDecodeError:
        return combined


def _trace_preview(value: Any, *, depth: int = 0) -> Any:
    if depth > 3:
        return "..."
    if isinstance(value, dict):
        preview: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 8:
                preview["..."] = f"{len(value) - 8} more keys"
                break
            preview[key] = _trace_preview(item, depth=depth + 1)
        return preview
    if isinstance(value, list):
        preview_items = [_trace_preview(item, depth=depth + 1) for item in value[:5]]
        if len(value) > 5:
            preview_items.append(f"... {len(value) - 5} more items")
        return preview_items
    if isinstance(value, str):
        return value if len(value) <= 160 else value[:157] + "..."
    return value


def _append_trace(trace: list[dict[str, Any]] | None, entry: dict[str, Any]) -> None:
    if trace is None:
        return
    trace.append({"timestamp": datetime.now(UTC).isoformat(timespec="seconds"), **entry})


async def call_tool(
    module_name: str,
    tool_name: str,
    arguments: dict[str, Any],
    trace: list[dict[str, Any]] | None = None,
) -> Any:
    _append_trace(
        trace,
        {
            "direction": "client->server",
            "transport": "stdio",
            "server": module_name,
            "tool": tool_name,
            "payload": {
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": _trace_preview(arguments)},
            },
        },
    )
    async with open_mcp_session(module_name) as session:
        result = await session.call_tool(tool_name, arguments=arguments)
    if getattr(result, "isError", False):
        _append_trace(
            trace,
            {
                "direction": "server->client",
                "transport": "stdio",
                "server": module_name,
                "tool": tool_name,
                "error": True,
                "payload": result.model_dump(mode="json"),
            },
        )
        raise RuntimeError(f"Tool call failed for {tool_name}")
    payload = _extract_tool_payload(result)
    _append_trace(
        trace,
        {
            "direction": "server->client",
            "transport": "stdio",
            "server": module_name,
            "tool": tool_name,
            "payload": _trace_preview(payload),
        },
    )
    return payload
