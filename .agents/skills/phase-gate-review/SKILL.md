---
name: phase-gate-review
description: >-
  Mandatory phase-gate retrospective invoked automatically whenever a TriVault
  implementation phase (Fase 1, 2, 3, or 4) is provisionally finished or before
  starting or proposing the next phase. Audits deliverables, security invariants,
  schema and API contracts, financial precision, tests, and CI readiness.
---

# TriVault Phase Gate Retrospective

Run this checklist **before** declaring any phase complete or moving to the next phase so architectural debt and security gaps never compound across phases.

## 1. Deliverables vs. Source of Truth
Compare the actual codebase against Section 7 of `CONTEXT.md` and `docs/especificacion-tecnica.md`:
- List every deliverable for the current phase and mark its real state: `COMPLETO`, `PARCIAL`, or `PENDIENTE`.
- Verify the phase acceptance criterion end-to-end (every user flow named in the criterion must have working backend endpoints, UI screens when required by the phase, and tests).

## 2. Database & Migration Portability Audit
- Confirm all 6 models or phase tables match `CONTEXT.md` Section 5.
- Confirm MySQL ↔ PostgreSQL portability: explicit `String(N)` lengths on indexed/`UNIQUE` columns, `native_enum=False` enums, `Numeric(12, 2)` / `Numeric(12, 4)` for financial quantities, `DateTime(timezone=True)`.
- Verify `alembic.ini` contains **zero credentials** and migrations run cleanly (`upgrade` and `downgrade` consistency).

## 3. Security & Isolation Audit
- **IDOR prevention**: Every read, update, and delete filters by `user_id == current_user.id` and returns `404 Not Found` (never `403`) on missing or foreign IDs.
- **Auth & JWT**: Password hashing uses `bcrypt` directly (no `passlib`), emails are normalized (`strip().lower()`), `/login` prevents user enumeration (identical `401` response), `get_current_user` validates signature, expiration, `type == "access"`, and active DB user existence.
- **CORS & Secrets**: `CORSMiddleware` uses explicit `ALLOWED_ORIGINS` (never `["*"]` in production); `git status` shows zero `.env`, keys, or hardcoded passwords in tracked files (`docker-compose.yml`, `config.py`, `alembic.ini`).

## 4. Financial Precision & Invariants Audit
- Zero `float` arithmetic for money or shares (`Decimal` throughout Python/Pydantic and `Numeric` in SQL).
- Multi-account updates (e.g., internal `transfer`, fund contributions) execute inside a single atomic DB transaction with rollback coverage.
- Protected fields (e.g., `current_balance` on `PATCH /accounts/{id}`) cannot be arbitrarily overwritten by client payloads.

## 5. Tests & CI Verification
- Run the actual test suite against the isolated test database (`trivault_test`) after the latest edits and report exact pass/fail counts.
- Verify negative security tests exist (expired/tampered tokens, IDOR cross-user access, rollback on failure, duplicate email/hash).
- Confirm frontend typecheck/build (`tsc`, `vite build`) and GitHub Actions CI checks when applicable to the phase.

## 6. Gate Verdict
End the retrospective with an explicit verdict:
- **APROBADA PARA AVANZAR**: All phase deliverables, security checks, and tests pass.
- **BLOQUEADA — GAPS PENDIENTES**: List the exact missing modules, endpoints, tests, or fixes required before advancing to the next phase, ordered by priority.
