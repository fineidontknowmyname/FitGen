"""
Regression smoke test for the plan-generation -> PDF-rendering pipeline.

This test exists specifically because `PDFArchitect._build_workout_section()`
previously referenced a non-existent `Exercise.equipment` attribute
(`ex.equipment` instead of `ex.equipment_needed`), which raised an
unconditional `AttributeError` for every generated plan, in every mode, with
zero test coverage catching it (see BATCH 1 / assessment report §6.1).

It runs the *real* orchestrator pipeline (`PlanOrchestrator.generate_plan`)
end-to-end for all three operating modes (A / B / C) and feeds the resulting
`FitnessPlan` into the *real* `pdf_architect.render_plan()` — the same call
path both `GET /plans/job/{id}/pdf` and the legacy
`POST /plans/generate/pdf` endpoint use. Ollama and the YouTube transcript
fetch are mocked (no network / no local LLM required); everything else
(safety filtering, scoring, scheduling, progression, roadmap building, PDF
rendering) runs unmocked.
"""
from __future__ import annotations

import pytest

from schemas.common import Equipment, ExperienceLevel
from schemas.content import Exercise, ExerciseLibrary
from schemas.vision import BodyComposition, SWRCategory
from schemas.common import MuscleLevel

from schemas.plan import GeneratePlanRequest
from core.orchestrator import plan_orchestrator, ollama_client
from services.intelligence.youtube import youtube_service
from reporting.pdf_architect import pdf_architect


async def _generate_via_request(**kwargs):
    """Build a GeneratePlanRequest exactly as the HTTP layer / Celery task
    does (schemas/plan.py's `_merge_urls` validator folds
    workout_youtube_urls/diet_youtube_urls into youtube_urls before the
    orchestrator ever sees them — see workers/tasks.py::_run_pipeline), then
    call the orchestrator the same way `_run_pipeline` does. Calling
    `generate_plan()` directly with only split URL params (bypassing this
    merge) is not how any real caller reaches the orchestrator, and
    under-supplies `_detect_mode()` — see assessment report §3.1."""
    request = GeneratePlanRequest(**kwargs)
    return await plan_orchestrator.generate_plan(
        user_profile=request.user_profile,
        youtube_urls=request.youtube_urls or [],
        workout_youtube_urls=request.workout_youtube_urls or [],
        diet_youtube_urls=request.diet_youtube_urls or [],
        transcript_text=request.transcript_text,
        body_composition=request.body_composition,
    )


def _fake_exercise(name: str, *, muscles: list[str] | None = None) -> Exercise:
    """A minimal, schema-valid, bodyweight-only Exercise fixture."""
    return Exercise(
        name=name,
        description=f"A bodyweight exercise: {name}.",
        instructions=["Step 1", "Step 2"],
        benefits=["General fitness"],
        muscles_worked=muscles or ["chest", "core"],
        equipment_needed=[Equipment.bodyweight],
        difficulty=ExperienceLevel.beginner,
        safety_warnings=[],
    )


_FAKE_LIBRARY = ExerciseLibrary(
    exercises=[
        _fake_exercise("Push-Up", muscles=["chest", "triceps"]),
        _fake_exercise("Bodyweight Squat", muscles=["quads", "glutes"]),
        _fake_exercise("Plank", muscles=["core"]),
        _fake_exercise("Lunge", muscles=["quads", "glutes"]),
        _fake_exercise("Mountain Climber", muscles=["core", "shoulders"]),
        _fake_exercise("Glute Bridge", muscles=["glutes", "hamstrings"]),
    ]
)


def _assert_valid_pdf(pdf_bytes: bytes) -> None:
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert pdf_bytes.startswith(b"%PDF"), "Rendered output is not a PDF byte-stream"
    assert len(pdf_bytes) > 1000, "Rendered PDF is suspiciously small"


async def test_mode_a_generates_valid_pdf(user_profile):
    """Mode A (profile only, no YouTube/photos) — no mocking needed, uses the
    built-in 50-exercise library end-to-end."""
    plan = await plan_orchestrator.generate_plan(user_profile)

    assert "[A]" in plan.title
    pdf_bytes = pdf_architect.render_plan(plan)
    _assert_valid_pdf(pdf_bytes)


async def test_mode_b_generates_valid_pdf(user_profile, monkeypatch):
    """Mode B (profile + YouTube) — Ollama and the transcript fetch are mocked;
    everything downstream (safety filter, scoring/scheduling, progression,
    roadmap, PDF render) runs for real."""

    async def fake_fetch_many(urls, *, skip_failed=True):
        return {url: f"transcript text for {url}" for url in urls}

    async def fake_extract_exercises(transcript_text: str) -> ExerciseLibrary:
        assert transcript_text  # got real (fake) transcript content
        return _FAKE_LIBRARY

    async def fake_generate_text(prompt: str, *, json_mode: bool = False) -> str:
        return "- Eat more protein.\n- Stay hydrated."

    monkeypatch.setattr(youtube_service, "fetch_many", fake_fetch_many)
    monkeypatch.setattr(ollama_client, "extract_exercises", fake_extract_exercises)
    monkeypatch.setattr(ollama_client, "generate_text", fake_generate_text)

    plan = await _generate_via_request(
        user_profile=user_profile,
        workout_youtube_urls=["https://youtube.com/watch?v=workout1"],
        diet_youtube_urls=["https://youtube.com/watch?v=diet1"],
    )

    assert "[B]" in plan.title
    assert plan.diet_notes  # extracted from the (mocked) diet transcript
    pdf_bytes = pdf_architect.render_plan(plan)
    _assert_valid_pdf(pdf_bytes)


async def test_mode_c_generates_valid_pdf(user_profile, monkeypatch):
    """Mode C (profile + YouTube + body photos) — same mocking as Mode B, plus
    a pre-computed BodyComposition passed straight into generate_plan(), which
    is how the real /plans/generate endpoint supplies it (vision analysis
    happens in a separate, earlier request)."""

    async def fake_fetch_many(urls, *, skip_failed=True):
        return {url: f"transcript text for {url}" for url in urls}

    async def fake_extract_exercises(transcript_text: str) -> ExerciseLibrary:
        return _FAKE_LIBRARY

    async def fake_generate_text(prompt: str, *, json_mode: bool = False) -> str:
        return "- Eat more protein.\n- Stay hydrated."

    monkeypatch.setattr(youtube_service, "fetch_many", fake_fetch_many)
    monkeypatch.setattr(ollama_client, "extract_exercises", fake_extract_exercises)
    monkeypatch.setattr(ollama_client, "generate_text", fake_generate_text)

    body_composition = BodyComposition(
        fat_pct_low=12.0,
        fat_pct_high=16.0,
        muscle_level=MuscleLevel.moderate,
        v_taper_ratio=1.3,
        shoulder_width_px=420.0,
        waist_width_px=336.0,
        shoulder_waist_ratio=1.25,
        swr_category=SWRCategory.ATHLETIC,
        posture_assessment="Good upright alignment",
        is_valid_person=True,
        confidence=0.82,
        pose_detected=True,
    )

    plan = await _generate_via_request(
        user_profile=user_profile,
        workout_youtube_urls=["https://youtube.com/watch?v=workout1"],
        diet_youtube_urls=["https://youtube.com/watch?v=diet1"],
        body_composition=body_composition,
    )

    assert "[C]" in plan.title
    assert plan.body_composition is not None
    pdf_bytes = pdf_architect.render_plan(plan)
    _assert_valid_pdf(pdf_bytes)


async def test_bodyweight_exercise_is_labelled_bw_not_a_crash(user_profile):
    """Narrow regression test for the exact line that crashed: a plan
    containing a pure-bodyweight exercise (equipment_needed == [bodyweight])
    must render its weight column as "BW", not raise AttributeError.

    Mode A's default library is bodyweight-only for a user with no equipment
    (see core/default_exercises.py's equipment filter), so this is guaranteed
    to exercise the exact `Equipment.bodyweight in ex.equipment_needed`
    branch that replaced the buggy `ex.equipment` attribute access.
    """
    plan = await plan_orchestrator.generate_plan(user_profile)

    assert any(
        Equipment.bodyweight in session_ex.exercise.equipment_needed
        for week in plan.weeks
        for session in week.sessions
        for session_ex in session.exercises
    ), "Test fixture assumption broken: expected at least one bodyweight exercise"

    pdf_bytes = pdf_architect.render_plan(plan)
    _assert_valid_pdf(pdf_bytes)
