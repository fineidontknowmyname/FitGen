from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from core.self_assessment import score_self_assessment
from core.tape_measurement import navy_body_fat_range
from schemas.body_input import SelfAssessmentRequest, TapeMeasurementRequest
from schemas.vision import BodyComposition, BodyCompositionSource, InputCompleteness

log = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/tape-measurement",
    response_model=BodyComposition,
    summary="Body composition from tape-measured circumferences (US Navy method)",
)
async def tape_measurement(body: TapeMeasurementRequest) -> BodyComposition:
    try:
        fat_low, fat_high = navy_body_fat_range(
            neck_cm=body.neck_cm,
            waist_cm=body.waist_cm,
            height_cm=body.height_cm,
            gender=body.gender.value,
            hip_cm=body.hip_cm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    log.info(
        "tape-measurement: gender=%s neck=%.1f waist=%.1f hip=%s height=%.1f -> fat_pct=%.1f-%.1f",
        body.gender.value, body.neck_cm, body.waist_cm, body.hip_cm, body.height_cm,
        fat_low, fat_high,
    )

    return BodyComposition(
        fat_pct_low=fat_low,
        fat_pct_high=fat_high,
        muscle_level=None,
        muscle_level_confidence=0.0,
        is_valid_person=True,
        confidence=0.85,
        pose_detected=False,
        waist_source="manual",
        hip_source="manual" if body.hip_cm is not None else "estimated",
        source=BodyCompositionSource.tape_measurement,
        input_completeness=InputCompleteness.full,
    )


@router.post(
    "/self-assessment",
    response_model=BodyComposition,
    summary="Body composition from a guided self-assessment questionnaire",
)
async def self_assessment(body: SelfAssessmentRequest) -> BodyComposition:
    result = score_self_assessment(
        visible_muscle_separation=body.visible_muscle_separation,
        vascularity=body.vascularity,
        body_fat_impression=body.body_fat_impression,
        perceived_muscle_mass=body.perceived_muscle_mass,
        experience_level=body.experience_level,
        pushup_count=body.pushup_count,
        squat_count=body.squat_count,
    )

    log.info(
        "self-assessment: muscle_level=%s confidence=%.3f",
        result.muscle_level.value, result.muscle_level_confidence,
    )

    completeness = (
        InputCompleteness.full
        if body.pushup_count is not None and body.squat_count is not None
        else InputCompleteness.partial
    )

    return BodyComposition(
        fat_pct_low=result.fat_pct_low,
        fat_pct_high=result.fat_pct_high,
        muscle_level=result.muscle_level,
        muscle_level_confidence=result.muscle_level_confidence,
        is_valid_person=True,
        confidence=result.muscle_level_confidence,
        pose_detected=False,
        source=BodyCompositionSource.self_assessment,
        input_completeness=completeness,
    )
