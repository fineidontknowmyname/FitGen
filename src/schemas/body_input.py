from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from schemas.common import ExperienceLevel, Gender


class MuscleSeparation(str, Enum):
    none = "none"
    slight = "slight"
    moderate = "moderate"
    defined = "defined"
    very_defined = "very_defined"


class Vascularity(str, Enum):
    none = "none"
    slight = "slight"
    moderate = "moderate"
    high = "high"


class BodyFatImpression(str, Enum):
    not_visible = "not_visible"
    partially_visible = "partially_visible"
    visible = "visible"
    very_visible = "very_visible"


class PerceivedMuscleMass(str, Enum):
    below_average = "below_average"
    average = "average"
    above_average = "above_average"
    well_above_average = "well_above_average"


class TapeMeasurementRequest(BaseModel):
    neck_cm: float = Field(ge=15.0, le=80.0)
    waist_cm: float = Field(ge=30.0, le=250.0)
    hip_cm: Optional[float] = Field(default=None, ge=30.0, le=250.0)
    height_cm: float = Field(ge=95.0, le=250.0)
    gender: Gender

    @model_validator(mode="after")
    def _require_hip_for_female(self) -> "TapeMeasurementRequest":
        if self.gender == Gender.female and self.hip_cm is None:
            raise ValueError("hip_cm is required when gender is 'female'.")
        return self


class SelfAssessmentRequest(BaseModel):
    visible_muscle_separation: MuscleSeparation
    vascularity: Vascularity
    body_fat_impression: BodyFatImpression
    perceived_muscle_mass: PerceivedMuscleMass
    experience_level: ExperienceLevel
    pushup_count: Optional[int] = Field(default=None, ge=0, le=200)
    squat_count: Optional[int] = Field(default=None, ge=0, le=200)
