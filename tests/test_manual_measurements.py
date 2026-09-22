import pytest

from services.vision.body_composition import _InferenceEngine, BodyCompositionService
from schemas.vision import BodyCompositionSource, InputCompleteness


def test_manual_waist_cm_overrides_photo_estimate(fake_mediapipe_pose, blank_image):
    engine = _InferenceEngine()

    estimated = engine._landmark_metrics(blank_image, user_height_cm=175.0, gender="male")
    fat_estimated = estimated[0]

    manual = engine._landmark_metrics(
        blank_image, user_height_cm=175.0, gender="male", manual_waist_cm=80.0
    )
    fat_manual = manual[0]

    expected = max(3.0, min(50.0, 64.0 - (20.0 * (175.0 / 80.0))))
    assert fat_manual == pytest.approx(expected, abs=0.01)
    assert fat_manual != pytest.approx(fat_estimated, abs=0.01)


def test_manual_waist_cm_differs_by_gender_constant(fake_mediapipe_pose, blank_image):
    engine = _InferenceEngine()

    male = engine._landmark_metrics(
        blank_image, user_height_cm=175.0, gender="male", manual_waist_cm=80.0
    )
    female = engine._landmark_metrics(
        blank_image, user_height_cm=175.0, gender="female", manual_waist_cm=80.0
    )

    assert male[0] != pytest.approx(female[0], abs=0.01)


def test_manual_hip_cm_overrides_v_taper(fake_mediapipe_pose, blank_image):
    engine = _InferenceEngine()

    estimated = engine._landmark_metrics(blank_image, user_height_cm=175.0, gender="male")
    v_taper_estimated = estimated[1]

    manual = engine._landmark_metrics(
        blank_image, user_height_cm=175.0, gender="male", manual_hip_cm=110.0
    )
    v_taper_manual = manual[1]

    assert v_taper_manual != pytest.approx(v_taper_estimated, abs=0.001)


def test_manual_waist_cm_zero_is_honoured_not_treated_as_unset(fake_mediapipe_pose, blank_image):
    engine = _InferenceEngine()

    estimated = engine._landmark_metrics(blank_image, user_height_cm=175.0, gender="male")
    fat_estimated = estimated[0]

    manual_zero = engine._landmark_metrics(
        blank_image, user_height_cm=175.0, gender="male", manual_waist_cm=0.0
    )
    fat_manual_zero = manual_zero[0]

    assert fat_manual_zero == pytest.approx(3.0, abs=0.01)
    assert fat_manual_zero != pytest.approx(fat_estimated, abs=0.01)


async def test_analyze_reports_manual_waist_source(fake_mediapipe_pose, blank_image):
    import cv2
    ok, encoded = cv2.imencode(".jpg", blank_image)
    assert ok
    image_bytes = encoded.tobytes()

    service = BodyCompositionService()
    result = await service.analyze(
        images=[image_bytes],
        user_height_cm=175.0,
        gender="male",
        manual_waist_cm=80.0,
    )

    assert result.waist_source == "manual"
    assert result.hip_source == "estimated"
    assert result.source == BodyCompositionSource.photo_plus_manual


async def test_analyze_reports_estimated_source_when_no_manual_input(
    fake_mediapipe_pose, blank_image
):
    import cv2
    ok, encoded = cv2.imencode(".jpg", blank_image)
    assert ok
    image_bytes = encoded.tobytes()

    service = BodyCompositionService()
    result = await service.analyze(
        images=[image_bytes],
        user_height_cm=175.0,
        gender="male",
    )

    assert result.waist_source == "estimated"
    assert result.hip_source == "estimated"
    assert result.source == BodyCompositionSource.photo_analysis
    assert result.input_completeness == InputCompleteness.partial
