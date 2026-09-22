import numpy as np
import pytest

from schemas.common import ActivityLevel, ExperienceLevel, FitnessGoal, Gender
from schemas.user import PhysicalActivity, StrengthMetrics, UserMetrics, UserProfile


@pytest.fixture
def user_profile() -> UserProfile:
    return UserProfile(
        biometrics=UserMetrics(age=28, weight_kg=80.0, height_cm=178.0, gender=Gender.male),
        metrics=StrengthMetrics(pushup_count=25, situp_count=20, squat_count=30),
        physical_activity=PhysicalActivity(
            activity_level=ActivityLevel.moderately_active,
            physical_activity_hours_per_day=1.0,
        ),
        injuries=[],
        equipment=[],
        experience_level=ExperienceLevel.intermediate,
        fitness_goal=FitnessGoal.muscle_gain,
    )


class _FakeLandmark:
    def __init__(self, x, y, z=0.0, visibility=0.9):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility


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


class _FakePoseLandmarkerResult:
    def __init__(self, landmarks):
        self.pose_landmarks = [landmarks] if landmarks else []


class _FakePoseLandmarker:
    def __init__(self, landmarks):
        self._landmarks = landmarks

    def detect(self, mp_image):
        return _FakePoseLandmarkerResult(self._landmarks)

    def close(self):
        pass


@pytest.fixture
def fake_mediapipe_pose(monkeypatch):
    from services.vision.model_loader import model_registry

    def _fake_create_pose_landmarker():
        return _FakePoseLandmarker(_make_33_landmarks())

    monkeypatch.setattr(model_registry, "create_pose_landmarker", _fake_create_pose_landmarker)


@pytest.fixture
def blank_image():
    return np.zeros((480, 640, 3), dtype=np.uint8)
