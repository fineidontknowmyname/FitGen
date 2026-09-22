from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Optional

from schemas.common import ExperienceLevel, MuscleLevel
from schemas.body_input import (
    BodyFatImpression,
    MuscleSeparation,
    PerceivedMuscleMass,
    Vascularity,
)

_CONFIDENCE_CEILING = 0.60

_MUSCLE_SEPARATION_SCORES = {
    "none": 0.0, "slight": 1.0, "moderate": 2.0, "defined": 3.0, "very_defined": 4.0,
}
_VASCULARITY_SCORES = {
    "none": 0.0, "slight": 1.0, "moderate": 2.0, "high": 3.0,
}
_BODY_FAT_IMPRESSION_SCORES = {
    "not_visible": 0.0, "partially_visible": 1.0, "visible": 2.0, "very_visible": 3.0,
}
_PERCEIVED_MUSCLE_MASS_SCORES = {
    "below_average": 0.0, "average": 1.0, "above_average": 2.0, "well_above_average": 3.0,
}
_EXPERIENCE_SCORES = {
    ExperienceLevel.beginner: 0.0, ExperienceLevel.intermediate: 1.0, ExperienceLevel.advanced: 2.0,
}

_BODY_FAT_IMPRESSION_RANGE = {
    "not_visible": (22.0, 30.0),
    "partially_visible": (16.0, 22.0),
    "visible": (10.0, 16.0),
    "very_visible": (6.0, 10.0),
}

_MUSCLE_LEVEL_BANDS = [
    (0.70, MuscleLevel.very_high),
    (0.52, MuscleLevel.high),
    (0.34, MuscleLevel.moderate),
    (0.00, MuscleLevel.low),
]


@dataclass
class SelfAssessmentResult:
    muscle_level: MuscleLevel
    muscle_level_confidence: float
    fat_pct_low: Optional[float]
    fat_pct_high: Optional[float]


def _strength_bonus(pushup_count: Optional[int], squat_count: Optional[int]) -> float:
    if pushup_count is None and squat_count is None:
        return 0.0
    parts = []
    if pushup_count is not None:
        parts.append(min(1.0, pushup_count / 40.0))
    if squat_count is not None:
        parts.append(min(1.0, squat_count / 50.0))
    return 2.0 * (sum(parts) / len(parts))


def score_self_assessment(
    visible_muscle_separation: MuscleSeparation,
    vascularity: Vascularity,
    body_fat_impression: BodyFatImpression,
    perceived_muscle_mass: PerceivedMuscleMass,
    experience_level: ExperienceLevel,
    pushup_count: Optional[int] = None,
    squat_count: Optional[int] = None,
) -> SelfAssessmentResult:
    sub_scores_normalized = [
        _MUSCLE_SEPARATION_SCORES[visible_muscle_separation] / 4.0,
        _VASCULARITY_SCORES[vascularity] / 3.0,
        _BODY_FAT_IMPRESSION_SCORES[body_fat_impression] / 3.0,
        _PERCEIVED_MUSCLE_MASS_SCORES[perceived_muscle_mass] / 3.0,
    ]

    experience_bonus = _EXPERIENCE_SCORES[experience_level]
    strength_bonus = _strength_bonus(pushup_count, squat_count)

    raw_total = (
        _MUSCLE_SEPARATION_SCORES[visible_muscle_separation]
        + _VASCULARITY_SCORES[vascularity]
        + _BODY_FAT_IMPRESSION_SCORES[body_fat_impression]
        + _PERCEIVED_MUSCLE_MASS_SCORES[perceived_muscle_mass]
        + experience_bonus
        + strength_bonus
    )
    max_possible = 4.0 + 3.0 + 3.0 + 3.0 + 2.0 + 2.0
    normalized_total = raw_total / max_possible

    muscle_level = MuscleLevel.low
    for threshold, level in _MUSCLE_LEVEL_BANDS:
        if normalized_total >= threshold:
            muscle_level = level
            break

    spread = statistics.pstdev(sub_scores_normalized) if len(sub_scores_normalized) > 1 else 0.0
    consistency = max(0.0, 1.0 - min(1.0, spread * 2.0))
    confidence = round(_CONFIDENCE_CEILING * consistency, 3)

    fat_low, fat_high = _BODY_FAT_IMPRESSION_RANGE[body_fat_impression]

    return SelfAssessmentResult(
        muscle_level=muscle_level,
        muscle_level_confidence=confidence,
        fat_pct_low=fat_low,
        fat_pct_high=fat_high,
    )
