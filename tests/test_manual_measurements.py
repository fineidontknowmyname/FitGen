import numpy as np
import pytest

from services.vision.body_composition import _InferenceEngine, BodyCompositionService


class _FakeLandmark:
    def __init__(self, x, y, z=0.0, visibility=0.9):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility


class _FakePoseLandmarks:
    def __init__(self, landmarks):
        self.landmark = landmarks


class _FakePoseResults:
    def __init__(self, landmarks):
        self.pose_landmarks = _FakePoseLandmarks(landmarks)


def _make_33_landmarks():
    blank = _FakeLandmark(0.5, 0.5)
    lms = [blank] * 33
    lms[11] = _FakeLandmark(0.3, 0.3)
    lms[12] = _FakeLandmark(0.7, 0.3)
    lms[23] = _FakeLandmark(0.4, 0.6)
    lms[24] = _FakeLandmark(0.6, 0.6)
    lms[27] = _FakeLandmark(0.4, 0.95)
    lms[28] = _FakeLandmark(0.6, 0.95)
    return lms


class _FakePose:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def process(self, img_rgb):
        return _FakePoseResults(_make_33_landmarks())


@pytest.fixture
def fake_mediapipe_pose(monkeypatch):
    import types
    import mediapipe as mp

    fake_pose_module = types.SimpleNamespace(Pose=_FakePose)
    fake_solutions = types.SimpleNamespace(pose=fake_pose_module)
    monkeypatch.setattr(mp, "solutions", fake_solutions, raising=False)


@pytest.fixture
def blank_image():
    return np.zeros((480, 640, 3), dtype=np.uint8)


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


async def test_analyze_reports_manual_waist_source(fake_mediapipe_pose, blank_image, monkeypatch):
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
