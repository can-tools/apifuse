# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-12
**Phase:** 1-Foundation
**Areas discussed:** Logging format, Settings strictness, CORS policy, Error response verbosity

---

## Logging Format

| Option | Description | Selected |
|--------|-------------|----------|
| JSON everywhere | Always emit JSON — consistent, no mode-switching, log aggregator-friendly from day one | |
| Human-readable in dev, JSON in prod | ConsoleRenderer when APP_ENV=development, JSONRenderer otherwise | ✓ |
| Human-readable always | Plain text output everywhere — simple but no log aggregator compatibility | |
| You decide | Let planner pick the most common FastAPI/structlog convention | |

**User's choice:** Human-readable in dev, JSON in prod
**Notes:** User asked for example format comparisons before deciding. After seeing the formats, chose the dev/prod split. Log level: DEBUG in dev, INFO in prod (also APP_ENV-driven).

---

## Settings Strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Only APP_ENV required | One required var: APP_ENV=development or production | |
| No required vars — all defaults | Application starts without any .env. APP_ENV defaults to development | ✓ |
| You decide | Planner picks the most sensible pydantic-settings approach | |

**User's choice:** No required vars — everything has sensible defaults
**Notes:** User clarified mid-question that CORS origins confused them. After explanation, user stated: API should work locally by default, blocking/restrictions should be optional, and security hardening should be deferred to a completely different phase. This shaped both this decision and the CORS decision.

---

## CORS Policy

| Option | Description | Selected |
|--------|-------------|----------|
| Open (*) permanently or until configured | allow_origins=["*"] — open API gateway by design | ✓ |
| Open (*) with CORS_ORIGINS override | Default *, but CORS_ORIGINS env var overrides if set | |
| You decide | Planner picks suitable approach for API gateway | |

**User's choice:** Open (`*`) permanently (or until explicitly configured in a future phase)
**Notes:** Directly informed by Settings discussion — user said restrictions belong in a later stage of development.

---

## Error Response Verbosity

| Option | Description | Selected |
|--------|-------------|----------|
| Details in dev, minimal in prod | Full exception message + type in dev; {"error": "...", "status_code": N} in prod | ✓ |
| Always minimal | {"error": "Internal server error", "status_code": 500} everywhere | |
| Always detailed | Full traceback always — easiest to debug, unsafe in prod | |

**User's choice:** Details in dev, minimal in prod
**Notes:** Standard dev/prod split following the same APP_ENV pattern. Error format chosen: `{"error": "<message>", "status_code": <code>}` (flat, simple, not FastAPI's `{"detail": ...}` format).

---

## Claude's Discretion

- Specific structlog processor chain (which processors before the renderer)
- Whether `logging.py` exposes a `configure_logging()` function or uses module-level setup
- Lifespan handler structure inside `main.py` — inline or helper function

## Deferred Ideas

- CORS allowlist / origin restriction — future phase (security hardening)
- Authentication / authorization — explicitly out of v1 scope
- Rate limiting — out of v1 scope
- `APIResponse` / `ErrorResponse` base models (MOD-01, MOD-02) — deferred to v2
- pytest suite (TEST-01/02/03) — deferred to v2
