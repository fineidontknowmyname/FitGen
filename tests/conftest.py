import types

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
    import mediapipe as mp

    fake_pose_module = types.SimpleNamespace(Pose=_FakePose)
    fake_solutions = types.SimpleNamespace(pose=fake_pose_module)
    monkeypatch.setattr(mp, "solutions", fake_solutions, raising=False)


@pytest.fixture
def blank_image():
    return np.zeros((480, 640, 3), dtype=np.uint8)
