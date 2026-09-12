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
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000


async def test_mode_a_generates_valid_pdf(user_profile):
    plan = await plan_orchestrator.generate_plan(user_profile)

    assert "[A]" in plan.title
    pdf_bytes = pdf_architect.render_plan(plan)
    _assert_valid_pdf(pdf_bytes)


async def test_mode_b_generates_valid_pdf(user_profile, monkeypatch):
    async def fake_fetch_many(urls, *, skip_failed=True):
        return {url: f"transcript text for {url}" for url in urls}

    async def fake_extract_exercises(transcript_text: str) -> ExerciseLibrary:
        assert transcript_text
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
    assert plan.diet_notes
    pdf_bytes = pdf_architect.render_plan(plan)
    _assert_valid_pdf(pdf_bytes)


async def test_mode_c_generates_valid_pdf(user_profile, monkeypatch):
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
    plan = await plan_orchestrator.generate_plan(user_profile)

    assert any(
        Equipment.bodyweight in session_ex.exercise.equipment_needed
        for week in plan.weeks
        for session in week.sessions
        for session_ex in session.exercises
    )

    pdf_bytes = pdf_architect.render_plan(plan)
    _assert_valid_pdf(pdf_bytes)
