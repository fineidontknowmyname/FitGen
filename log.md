# Comment Log

Rationale and explanatory notes that would otherwise be inline code comments, kept here instead per standing instruction. Organized by batch, referencing the assessment report's section numbers.

## Batch 1 — PDF crash fix + regression test

- `src/reporting/pdf_architect.py`, `_build_workout_section()`: `ex.equipment` was replaced with `Equipment.bodyweight in ex.equipment_needed` because `Exercise` (schemas/content.py) has no `equipment` attribute — only `equipment_needed: List[Equipment]`. The pre-existing `workout_exercise.sets[0].weight_kg <= 0` fallback check is kept as an OR-condition, unchanged.
- Deliberately out of scope for this batch: `orchestrator.py`'s flat-schedule bodyweight-weight bug (hardcoded `weight_kg=10.0` for every exercise) and the two-schedule-representation issue — both entangled with this same render function, deferred to Batch 4 per the assessment's dependency graph.
- `tests/test_pdf_smoke.py`: runs the real `PlanOrchestrator.generate_plan()` end-to-end for modes A/B/C (Ollama + YouTube fetch mocked for B/C, everything else real), then feeds the result through the real `pdf_architect.render_plan()`, asserting valid PDF bytes with no exception. A narrow test also targets the bodyweight-exercise label path specifically. Modes B/C build a `GeneratePlanRequest` and mirror `workers/tasks.py::_run_pipeline`'s call shape rather than calling the orchestrator directly with only split URL params — calling it directly under-supplies `_detect_mode()` (see the §3.1 latent edge case noted in the assessment: `_detect_mode` only inspects `youtube_urls`/`transcript_text`, not `workout_youtube_urls`/`diet_youtube_urls`; the HTTP schema's `_merge_urls` validator is what normally reconciles this).
- Verified (then reverted) that these tests fail with the original `AttributeError` before the fix, and pass after — confirming the tests actually catch the regression.

## Batch 2 — Login validation + profilePayload field-naming fix

- `src/schemas/user.py`, `LoginRequest`: password has `min_length=1`, not 8. Login is a credential *check* against an already-stored hash, not a password-creation flow — an account created under an earlier or different password policy (or a future policy change) should still be able to log in with whatever password it was actually given at signup time. The 8-char minimum belongs to `SignupRequest` only.
- `src/api/v1/endpoints/users.py`, `login()`: request body changed from a raw `dict` to `LoginRequest`, matching every other endpoint in this file's use of typed Pydantic bodies. Malformed bodies (missing/wrong-typed fields) now get a standard 422 instead of silently coercing to empty strings via `.get(...)`.
- `frontend/src/lib/profilePayload.ts`, `buildProfilePayload()`: the null-user fallback branch returned a field named `equipment`; the populated-user branch returns `equipment_available`. Backend (`GeneratePlanRequest` → `UserProfile`) expects `equipment_available` — the null branch's key was simply wrong, not a deliberate alternate shape. Renamed to match.
- `frontend/src/lib/profilePayload.test.ts`: the existing test asserted `payload.equipment` for the null-user case, locking in the wrong key name rather than catching it. Updated to assert `payload.equipment_available`.
