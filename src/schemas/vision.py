from enum import Enum

from pydantic import BaseModel, Field
from typing import Optional
from schemas.common import MuscleLevel, BodyType


class SWRCategory(str, Enum):
    OVERFAT  = "overfat"
    BALANCED = "balanced"
    ATHLETIC = "athletic"


class BodyCompositionSource(str, Enum):
    photo_analysis     = "photo_analysis"
    photo_plus_manual  = "photo_plus_manual"
    tape_measurement   = "tape_measurement"
    self_assessment     = "self_assessment"
    unavailable         = "unavailable"


class InputCompleteness(str, Enum):
    full    = "full"
    partial = "partial"


class BodyComposition(BaseModel):

    fat_pct_low: Optional[float] = Field(
        None, ge=2.0, le=60.0,
        description="Lower bound of estimated body fat percentage"
    )
    fat_pct_high: Optional[float] = Field(
        None, ge=2.0, le=60.0,
        description="Upper bound of estimated body fat percentage"
    )

    muscle_level: Optional[MuscleLevel] = Field(
        None, description="Estimated muscle mass level"
    )
    body_type: Optional[BodyType] = Field(
        None, description="Estimated somatotype: ectomorph | mesomorph | endomorph"
    )

    v_taper_ratio: Optional[float] = Field(
        None, ge=0.5, le=3.0,
        description="Estimated shoulder-width / waist-width ratio"
    )

    shoulder_width_px: float = Field(
        default=0.0, ge=0.0,
        description="Pixel-space shoulder width (landmarks 11–12)"
    )
    waist_width_px: float = Field(
        default=0.0, ge=0.0,
        description="Pixel-space waist/hip width (landmarks 23–24)"
    )
    shoulder_waist_ratio: float = Field(
        default=1.1, ge=0.0,
        description="Shoulder width ÷ waist width"
    )
    swr_category: SWRCategory = Field(
        default=SWRCategory.BALANCED,
        description="Classification: overfat | balanced | athletic"
    )

    posture_assessment: Optional[str] = Field(
        None, max_length=200,
        description="Brief posture note e.g. 'Slight anterior pelvic tilt'"
    )

    is_valid_person: bool = Field(
        True,
        description="False if no clear full-body shot was detected"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall confidence in this analysis (landmark + muscle-classification blend)"
    )
    pose_detected: bool = Field(
        default=False,
        description=(
            "True if MediaPipe successfully found body landmarks in at least one image. "
            "False when stub/estimated values are used (e.g. image too small, "
            "no person visible, or mediapipe unavailable)."
        ),
    )

    waist_source: str = Field(
        default="estimated",
        description="'estimated' (from photo geometry) or 'manual' (user-supplied waist_cm)",
    )
    hip_source: str = Field(
        default="estimated",
        description="'estimated' (from photo geometry) or 'manual' (user-supplied hip_cm)",
    )

    source: BodyCompositionSource = Field(
        default=BodyCompositionSource.unavailable,
        description="Which input path produced this analysis",
    )
    muscle_level_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description=(
            "Confidence specifically in muscle_level (not the blended overall confidence). "
            "0.0 means genuinely unavailable — never a placeholder for a missing model."
        ),
    )
    input_completeness: InputCompleteness = Field(
        default=InputCompleteness.partial,
        description="'full' when enough input was supplied for a reliable read, else 'partial'",
    )

# Backward-compat alias so existing imports don't break
BodyAnalysisResult = BodyComposition
