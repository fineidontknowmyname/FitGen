# Comment Log

Rationale, explanations, and notes that would otherwise be inline code comments. Per project rule (Documents/memory.md, Rule 1), appended here instead — never in code. Migrated from the earlier `log.md` (pre-dating this rule file being found) and reformatted to the required entry format; `log.md` is left in place pending confirmation to remove it.

---

## src/reporting/pdf_architect.py — `_build_workout_section()`
Date: 2026-09-12
Note: `ex.equipment` was replaced with `Equipment.bodyweight in ex.equipment_needed` because `Exercise` (schemas/content.py) has no `equipment` attribute — only `equipment_needed: List[Equipment]`. The pre-existing `workout_exercise.sets[0].weight_kg <= 0` fallback check is kept as an OR-condition, unchanged. Deliberately out of scope for that batch: `orchestrator.py`'s flat-schedule bodyweight-weight bug (hardcoded `weight_kg=10.0` for every exercise) and the two-schedule-representation issue — both entangled with this same render function, deferred to a later batch per the assessment's dependency graph.

## tests/test_pdf_smoke.py
Date: 2026-09-12
Note: Runs the real `PlanOrchestrator.generate_plan()` end-to-end for modes A/B/C (Ollama + YouTube fetch mocked for B/C, everything else real), then feeds the result through the real `pdf_architect.render_plan()`, asserting valid PDF bytes with no exception. A narrow test also targets the bodyweight-exercise label path specifically. Modes B/C build a `GeneratePlanRequest` and mirror `workers/tasks.py::_run_pipeline`'s call shape rather than calling the orchestrator directly with only split URL params — calling it directly under-supplies `_detect_mode()` (it only inspects `youtube_urls`/`transcript_text`, not `workout_youtube_urls`/`diet_youtube_urls`; the HTTP schema's `_merge_urls` validator is what normally reconciles this). Verified (then reverted) that these tests fail with the original `AttributeError` before the fix, and pass after — confirming the tests actually catch the regression.

## src/schemas/user.py — `LoginRequest`
Date: 2026-09-12
Note: Password has `min_length=1`, not 8. Login is a credential *check* against an already-stored hash, not a password-creation flow — an account created under an earlier or different password policy (or a future policy change) should still be able to log in with whatever password it was actually given at signup time. The 8-char minimum belongs to `SignupRequest` only.

## src/api/v1/endpoints/users.py — `login()`
Date: 2026-09-12
Note: Request body changed from a raw `dict` to `LoginRequest`, matching every other endpoint in this file's use of typed Pydantic bodies. Malformed bodies (missing/wrong-typed fields) now get a standard 422 instead of silently coercing to empty strings via `.get(...)`.

## frontend/src/lib/profilePayload.ts — `buildProfilePayload()`
Date: 2026-09-12
Note: The null-user fallback branch returned a field named `equipment`; the populated-user branch returns `equipment_available`. Backend (`GeneratePlanRequest` → `UserProfile`) expects `equipment_available` — the null branch's key was simply wrong, not a deliberate alternate shape. Renamed to match.

## frontend/src/lib/profilePayload.test.ts
Date: 2026-09-12
Note: The existing test asserted `payload.equipment` for the null-user case, locking in the wrong key name rather than catching it. Updated to assert `payload.equipment_available`.

## src/services/vision/body_composition.py — `_landmark_metrics()`, `analyse_one()`, `BodyCompositionService.analyze()`
Date: 2026-09-22
Note: Prior to this change, `/vision/analyze-body` only ever estimated waist circumference from photo pixel geometry (shoulder/hip landmark midpoint distance × π), which the RFM body-fat formula then consumes — there was no path for a user to supply an actual tape-measured value. Added optional `manual_waist_cm`/`manual_hip_cm` params threaded through all three functions; when supplied, they're used directly in place of the pixel-estimated `waist_circ`/`hip_cm`, and everything downstream (RFM fat%, V-taper) is unchanged, it just consumes a more accurate input.

## src/schemas/vision.py — `BodyComposition`
Date: 2026-09-22
Note: Added `waist_source`/`hip_source` (`"estimated"` | `"manual"`) so the API response is honest about which value was actually used for each metric, rather than silently mixing manual and estimated values with no way to tell them apart.

## src/api/v1/endpoints/vision.py — `analyze_body()`
Date: 2026-09-22
Note: Added optional `waist_cm`/`hip_cm` form fields (`ge=30, le=250`), matching the sanity-bound style already used elsewhere in this codebase for body measurements.

## frontend/src/lib/api.ts — `uploadPhotos()`
Date: 2026-09-22
Note: Two new optional params, appended to the form data only when present — empty/NaN silently omitted rather than sent as `0`, since `0` would be a valid-looking but wrong measurement.

## frontend/src/app/onboarding/page.tsx — photos step
Date: 2026-09-22
Note: Added two optional number inputs (waist/hip, cm) with copy explaining they're optional and improve accuracy; results panel marks a metric "(measured)" when `waist_source`/`hip_source` come back `"manual"`. Deliberately not persisted into `localStorage['fitgen_user']`/`profilePayload.ts` — these are one-time calibration inputs for a single analysis call, the same treatment already given to `height`/`gender` in this flow, not part of the durable user profile.

## tests/test_manual_measurements.py
Date: 2026-09-22
Note: Unit tests against `_InferenceEngine._landmark_metrics()` directly, mocking MediaPipe's `Pose` class via a fake `mp.solutions.pose` namespace (see finding below) — confirms the manual value is used verbatim in the RFM formula and differs from the photo estimate, plus `BodyCompositionService.analyze()`-level tests confirming `waist_source`/`hip_source` are reported correctly.

## src/services/vision/landmarks.py & body_composition.py — MediaPipe compatibility (finding, not yet fixed)
Date: 2026-09-22
Note: The installed `mediapipe` version in this venv is `1.0.1` (per `requirements.lock.txt`), which has removed the legacy `mp.solutions` API entirely that both files are built on. `landmarks.py` has a defensive `try/except AttributeError` fallback to `mediapipe.python.solutions`, but that fallback module doesn't exist in this version either (`ModuleNotFoundError`), so it's also dead. `body_composition.py::_landmark_metrics()` has no such fallback at all. In practice this means real pose detection is currently failing for every request in this environment and silently degrading to stub/estimated values — the existing test `test_landmark_detector_returns_none_for_blank_image` currently passes for the wrong reason (an exception being swallowed, not a genuine "no person in a blank image" result). Pre-existing environment/dependency issue, orthogonal to the manual-measurement feature; not addressed as part of that change. Recorded as a formal Phase −1 in `Documents/body_composition_phase0_decisions.md`, required before Phase 4 (model training) but not blocking Phase 0/2.

## src/schemas/vision.py — `BodyCompositionSource`, `InputCompleteness`, `BodyComposition` (Phase 0)
Date: 2026-09-22
Note: Added additively — every pre-existing field is untouched, so nothing downstream (orchestrator, capacity engine, PDF renderer, frontend) needed to change to keep working. `source` has a 4th value beyond the original 3-path plan (`photo_plus_manual`) specifically to represent the hybrid mode already shipped (photo + one manually-typed measurement) without discarding the granular `waist_source`/`hip_source` fields — `source` answers "which flow," the granular fields answer "which specific number was typed in." See `Documents/body_composition_phase0_decisions.md` for the full reasoning (decision 1).

## src/services/vision/body_composition.py — muscle-level honesty fix + falsy-check bug fix (Phase 0)
Date: 2026-09-22
Note: Two fixes made while implementing Phase 0, found during a self-review of the manual-measurement change from the same day:
1. `analyse_one()`'s no-model branch previously set `muscle_level = MuscleLevel.moderate` — a hardcoded constant standing in for "no data," the single worst finding from the earlier assessment (§5.4). Now returns `None`, and `_fuse()`'s existing `Counter(...)`-based majority vote already handles an all-`None` input correctly (falls through to `None`) with no further change needed there.
2. `_ImageResult.muscle_score` held the real, muscle-classification-only confidence (before it gets blended with landmark confidence into the generic `confidence` field two lines later) but was never read anywhere — `_fuse()` now averages it (only over images where `muscle_level is not None`, so a missing-model image doesn't silently drag down the average for an image that did classify) and exposes it as `muscle_level_confidence`. This is real, already-computed data that existed in the pipeline and was simply discarded before this change, not a new estimate.
3. `if manual_waist_cm:` / `if manual_hip_cm:` (three call sites: twice in `_landmark_metrics`, twice in `analyze()`) used Python truthiness, not a None-check — `manual_waist_cm=0.0` would silently fall through to the photo estimate instead of being honoured. Currently unreachable via the live endpoint (`ge=30.0` on the Form field prevents 0 today) but a real footgun for Phase 2, which will call these same functions from a different endpoint with different validation. Changed to explicit `is not None` checks. Covered by `test_manual_waist_cm_zero_is_honoured_not_treated_as_unset`.

## src/services/vision/body_composition.py — `_fuse()` posture majority vote (Phase 0, closes §5.5)
Date: 2026-09-22
Note: `posture_assessment` was the one categorical field using `posture_vals[-1]` ("last (best angle)") instead of the `Counter(...).most_common(1)` majority vote every other categorical field (`muscle_level`, `body_type`, `swr_category`) already used — flagged as an inconsistency in the original assessment (§5.5). Switched to majority vote for consistency; on a tie, `Counter.most_common` keeps insertion order, so the first-seen value among the tied leaders wins (Python 3.7+ dict/Counter ordering guarantee).

## tests/conftest.py — shared MediaPipe-mocking fixtures
Date: 2026-09-22
Note: `fake_mediapipe_pose`/`blank_image` were duplicated in `test_manual_measurements.py` and needed again by the new `test_body_composition_contract.py` — moved to `conftest.py` so both share one definition rather than drifting apart. `test_manual_measurements.py` updated to drop its local copies.

## src/core/tape_measurement.py — Navy circumference method (Phase 2.2)
Date: 2026-09-22
Note: Pure function, no I/O — mirrors the existing `core/` engine style (`bmi.py`, `tdee.py`, one formula per file). `navy_body_fat_range()` adds a ±3.5% spread around the point estimate (min ±0.5 point) — that figure is the method's own published typical error versus DEXA, not an arbitrary number; it's deliberately much tighter than the photo path's ±15% band, reflecting that a measured circumference is more reliable than a pixel-estimated one. Raises `ValueError` on domain violations (`waist_cm <= neck_cm`, missing `hip_cm` for female, non-positive log10 input) rather than letting `math.log10` raise its own less-actionable `ValueError`/`domain error` — the endpoint converts this to a 422 with the message intact.

## src/core/self_assessment.py — deterministic scoring rubric (Phase 2.3)
Date: 2026-09-22
Note: Explicitly rule-based, not a model, per the plan's own instruction ("resist the temptation to train something for 5-7 categorical inputs"). Confidence is capped at 0.60 (`_CONFIDENCE_CEILING`) per Decision 3 in `Documents/body_composition_phase0_decisions.md` — self-report gets a materially lower ceiling than tape/photo regardless of how internally consistent the answers are, and is further reduced within that ceiling by response inconsistency (population stdev across the four normalized sub-scores). `fat_pct` range comes from a coarse, explicitly approximate lookup keyed on `body_fat_impression` alone (visible abs correlates loosely with body-fat percentage) — not intended to be precise, which is why the ranges are wide.

## src/schemas/body_input.py — `TapeMeasurementRequest`, `SelfAssessmentRequest` (Phase 2.2/2.3)
Date: 2026-09-22
Note: New file rather than adding to `schemas/vision.py` — these two requests have nothing to do with images/vision, they're the input side of the two new non-photo paths. `TapeMeasurementRequest`'s `hip_cm` is optional at the field level but enforced as required-for-female via a `model_validator`, matching the Navy method's own formula (male doesn't need hip; female does) — same pattern `UserProfile` already uses elsewhere in this codebase for conditional-required fields.

## src/api/v1/endpoints/metrics.py — tape-measurement + self-assessment endpoints (Phase 2.2/2.3)
Date: 2026-09-22
Note: Both stateless — compute-and-return, no DB write — matching the existing `/vision/analyze-body` endpoint's own pattern (Rule 7 consistency); a persisted "body composition history" isn't part of any endpoint yet, photo included, so these two don't invent one on their own. `tape_measurement()`'s `confidence=0.85` is a deliberate, documented choice (not a placeholder): the Navy method has known, published accuracy against DEXA, materially better than a photo-geometry guess and than self-report, which is why it isn't capped anywhere near the self-assessment path's 0.60 ceiling. `muscle_level=None`/`muscle_level_confidence=0.0` for tape measurement is honest, not a gap to fill later — this path fundamentally cannot measure muscle level (no image, no visual signal at all), unlike the photo path's `None` which specifically means "no trained model file, ideally would give a real answer."
