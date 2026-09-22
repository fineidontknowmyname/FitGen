import cv2
import pytest

from schemas.common import MuscleLevel
from schemas.vision import BodyComposition, BodyCompositionSource, InputCompleteness
from services.vision.body_composition import (
    BodyCompositionService,
    _ImageResult,
)


def test_schema_defaults_are_honest_not_placeholders():
    bc = BodyComposition()

    assert bc.source == BodyCompositionSource.unavailable
    assert bc.muscle_level_confidence == 0.0
    assert bc.input_completeness == InputCompleteness.partial
    assert bc.muscle_level is None


async def test_analyze_empty_images_reports_unavailable():
    service = BodyCompositionService()
    result = await service.analyze(images=[])

    assert result.is_valid_person is False
    assert result.source == BodyCompositionSource.unavailable
    assert result.muscle_level_confidence == 0.0
    assert result.input_completeness == InputCompleteness.partial


async def test_analyze_no_valid_person_reports_unavailable():
    service = BodyCompositionService()
    result = await service.analyze(images=[b"not a real image"])

    assert result.is_valid_person is False
    assert result.source == BodyCompositionSource.unavailable
    assert result.muscle_level_confidence == 0.0


async def test_analyze_two_valid_images_reports_full_completeness(
    fake_mediapipe_pose, blank_image
):
    ok, encoded = cv2.imencode(".jpg", blank_image)
    assert ok
    image_bytes = encoded.tobytes()

    service = BodyCompositionService()
    result = await service.analyze(images=[image_bytes, image_bytes])

    assert result.input_completeness == InputCompleteness.full


async def test_muscle_level_is_none_not_a_fake_constant_when_model_unavailable(
    fake_mediapipe_pose, blank_image
):
    ok, encoded = cv2.imencode(".jpg", blank_image)
    assert ok
    image_bytes = encoded.tobytes()

    service = BodyCompositionService()
    result = await service.analyze(images=[image_bytes])

    assert result.muscle_level is None
    assert result.muscle_level_confidence == 0.0


def test_fuse_majority_votes_posture_not_last_value():
    r1 = _ImageResult()
    r1.is_valid = True
    r1.posture = "Good upright alignment"

    r2 = _ImageResult()
    r2.is_valid = True
    r2.posture = "Good upright alignment"

    r3 = _ImageResult()
    r3.is_valid = True
    r3.posture = "Slight forward lean"

    fused = BodyCompositionService._fuse([r1, r2, r3])

    assert fused.posture_assessment == "Good upright alignment"


def test_fuse_muscle_level_confidence_averages_only_over_classified_images():
    r1 = _ImageResult()
    r1.is_valid = True
    r1.muscle_level = MuscleLevel.high
    r1.muscle_score = 0.8

    r2 = _ImageResult()
    r2.is_valid = True
    r2.muscle_level = None
    r2.muscle_score = 0.0

    fused = BodyCompositionService._fuse([r1, r2])

    assert fused.muscle_level_confidence == pytest.approx(0.8, abs=0.001)
