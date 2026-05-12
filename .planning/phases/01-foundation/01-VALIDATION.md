---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-12
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml [tool.pytest.ini_options]` — Wave 0 must create this section |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-xx | 01 | 0 | FOUND-01 | — | N/A | unit | `uv run pytest tests/test_config.py -x` | ❌ W0 | ⬜ pending |
| 01-01-xx | 01 | 0 | FOUND-01 | — | N/A | unit | `uv run pytest tests/test_config.py::test_no_env_file -x` | ❌ W0 | ⬜ pending |
| 01-01-xx | 01 | 0 | FOUND-02 | — | No print() leaks | static | `grep -rn "print(" app/ main.py` | ❌ W0 | ⬜ pending |
| 01-01-xx | 01 | 0 | FOUND-02 | T-prod-logs | Structured JSON in prod | unit | `uv run pytest tests/test_logging.py -x` | ❌ W0 | ⬜ pending |
| 01-01-xx | 01 | 1 | FOUND-03 | T-info-disc | Minimal errors in prod | smoke | `uv run uvicorn main:app --port 8765 &; sleep 1; curl -s http://localhost:8765/` | ❌ W0 | ⬜ pending |
| 01-01-xx | 01 | 1 | FOUND-03 | T-info-disc | JSON error envelope, not stack trace | integration | `uv run pytest tests/test_app.py::test_error_envelope -x` | ❌ W0 | ⬜ pending |
| 01-01-xx | 01 | 1 | FOUND-03 | — | CORS preflight handled | integration | `uv run pytest tests/test_app.py::test_cors_headers -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/conftest.py` — shared `TestClient` fixture using `httpx.AsyncClient(app=app, base_url="http://test")`
- [ ] `tests/test_config.py` — covers FOUND-01 (settings defaults, no env file)
- [ ] `tests/test_logging.py` — covers FOUND-02 (JSON output in prod mode)
- [ ] `tests/test_app.py` — covers FOUND-03 (CORS headers, error envelope, smoke)
- [ ] `pyproject.toml [tool.pytest.ini_options]` — `asyncio_mode = "auto"`, `testpaths = ["tests"]`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Human-readable console output in dev | FOUND-02 | Log format is visual, not machine-assertable | Run `uv run uvicorn main:app`, confirm colored/readable output in terminal |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
