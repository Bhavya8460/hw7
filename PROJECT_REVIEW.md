# Project Review (April 1, 2026)

## Overall verdict
The architecture and feature set are coherent: a CLI/UI orchestrates 3 MCP servers (travel, budget, calendar), stores trip data in SQLite, and exports both ICS + XLSX outputs. The project *does* make sense as an end-to-end MCP demo for practical trip planning.

That said, there are a few concrete issues worth fixing.

---

## Issues found

### 1) Missing runtime dependencies for the web UI
**Severity:** High  
`trip_operator/webapp.py` imports `uvicorn` and `starlette`, but these packages are not listed in `pyproject.toml` dependencies. Fresh installs using only the declared dependencies can fail when running `main.py ui`.

**Evidence**
- Uses: `import uvicorn` and `from starlette...` in `trip_operator/webapp.py`.
- Declared deps only include `httpx`, `mcp[cli]`, `openpyxl`.

**Suggested fix**
Add explicit dependencies:
- `starlette`
- `uvicorn`

---

### 2) README architecture links are machine-specific absolute paths
**Severity:** Medium  
The README "Architecture" section links to absolute local file paths (e.g., `/Users/bhavya/Desktop/...`). These links will be broken for everyone else (GitHub, classmates, CI, other machines).

**Suggested fix**
Replace with repository-relative links, e.g.:
- `./main.py`
- `./trip_operator/cli.py`

---

### 3) Expense CSV import is not atomic (partial imports possible)
**Severity:** Medium  
`import_expenses_from_csv` inserts each row one-by-one and raises on first invalid row. If a bad row appears in the middle, earlier rows remain committed, causing partial imports.

**Suggested fix**
Wrap CSV import in one database transaction so the import is all-or-nothing.

---

### 4) Python-version compatibility can be confusing in practice
**Severity:** Low (documentation/UX)  
The code intentionally targets Python 3.12+ (`requires-python = ">=3.12"`), and uses `datetime.UTC`, which breaks on Python 3.10. This is valid, but users running system Python 3.10 get a hard import failure unless they use a 3.12 venv.

**Suggested fix**
Keep 3.12 requirement, but improve error messaging in setup docs and CLI startup so users immediately know they need Python 3.12.

---

## What is working well
- Clear MCP orchestration boundaries (`workflows.py`) with explicit tool-call sequence.
- Sensible fallback behavior for geocoding/weather/rates.
- Good UX features: MCP trace view, structured dashboard, and Excel export.
- Data model is straightforward and easy to inspect (`trips` + `expenses`).

## Recommended next actions (priority order)
1. Add `starlette` + `uvicorn` to `pyproject.toml`.
2. Fix README links to relative paths.
3. Make CSV import transactional.
4. Add an explicit startup/version check or clearer docs for Python 3.12 requirement.
