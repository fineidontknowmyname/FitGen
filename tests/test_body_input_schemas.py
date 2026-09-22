import pytest
from pydantic import ValidationError

from schemas.body_input import (
    BodyFatImpression,
    MuscleSeparation,
    PerceivedMuscleMass,
    SelfAssessmentRequest,
    TapeMeasurementRequest,
    Vascularity,
)
from schemas.common import ExperienceLevel, Gender


def test_tape_measurement_male_does_not_require_hip():
    req = TapeMeasurementRequest(
        neck_cm=38.0, waist_cm=85.0, height_cm=178.0, gender=Gender.male
    )
    assert req.hip_cm is None


def test_tape_measurement_female_requires_hip():
    with pytest.raises(ValidationError):
        TapeMeasurementRequest(
            neck_cm=32.0, waist_cm=75.0, height_cm=165.0, gender=Gender.female
        )


def test_tape_measurement_female_with_hip_is_valid():
    req = TapeMeasurementRequest(
        neck_cm=32.0, waist_cm=75.0, height_cm=165.0, gender=Gender.female, hip_cm=95.0
    )
    assert req.hip_cm == 95.0


def test_tape_measurement_rejects_out_of_range_values():
    with pytest.raises(ValidationError):
        TapeMeasurementRequest(
            neck_cm=5.0, waist_cm=85.0, height_cm=178.0, gender=Gender.male
        )


def test_self_assessment_accepts_valid_input():
    req = SelfAssessmentRequest(
        visible_muscle_separation=MuscleSeparation.moderate,
        vascularity=Vascularity.slight,
        body_fat_impression=BodyFatImpression.partially_visible,
        perceived_muscle_mass=PerceivedMuscleMass.average,
        experience_level=ExperienceLevel.intermediate,
    )
    assert req.pushup_count is None


def test_self_assessment_rejects_invalid_enum_value():
    with pytest.raises(ValidationError):
        SelfAssessmentRequest(
            visible_muscle_separation="extremely_defined",
            vascularity=Vascularity.slight,
            body_fat_impression=BodyFatImpression.partially_visible,
            perceived_muscle_mass=PerceivedMuscleMass.average,
            experience_level=ExperienceLevel.intermediate,
        )
