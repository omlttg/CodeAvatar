# Scope: E2E Testing Track

## Architecture
- Opaque-box testing of CodeAvatar CLI (`pipeline_cli.py`) and FastAPI backend.
- Test runner: `pytest`.
- 4-Tier Test Suite structure.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Test Infrastructure Design | Analyze environment, design test structure, and write `TEST_INFRA.md`. | none | DONE |
| 2 | CLI E2E Tests | Implement Tier 1-4 tests for `pipeline_cli.py`. | M1 | IN_PROGRESS |
| 3 | API Backend E2E Tests | Implement Tier 1-4 tests for FastAPI backend (SQLite, queue, auth, SSE). | M1 | IN_PROGRESS |
| 4 | Verification & Audit | Run verification tests, fix import/syntax issues, run Forensic Auditor. | M2, M3 | PLANNED |
| 5 | Publish & Handover | Publish `TEST_READY.md` and send completion handoff. | M4 | PLANNED |
