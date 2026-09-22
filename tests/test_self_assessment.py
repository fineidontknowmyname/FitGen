from core.self_assessment import score_self_assessment
from schemas.body_input import BodyFatImpression, MuscleSeparation, PerceivedMuscleMass, Vascularity
from schemas.common import ExperienceLevel, MuscleLevel


def test_all_low_answers_yield_low_muscle_level():
    result = score_self_assessment(
        visible_muscle_separation=MuscleSeparation.none,
        vascularity=Vascularity.none,
        body_fat_impression=BodyFatImpression.not_visible,
        perceived_muscle_mass=PerceivedMuscleMass.below_average,
        experience_level=ExperienceLevel.beginner,
    )
    assert result.muscle_level == MuscleLevel.low


def test_all_high_answers_yield_very_high_muscle_level():
    result = score_self_assessment(
        visible_muscle_separation=MuscleSeparation.very_defined,
        vascularity=Vascularity.high,
        body_fat_impression=BodyFatImpression.very_visible,
        perceived_muscle_mass=PerceivedMuscleMass.well_above_average,
        experience_level=ExperienceLevel.advanced,
        pushup_count=50,
        squat_count=60,
    )
    assert result.muscle_level == MuscleLevel.very_high


def test_confidence_never_exceeds_ceiling():
    result = score_self_assessment(
        visible_muscle_separation=MuscleSeparation.very_defined,
        vascularity=Vascularity.high,
        body_fat_impression=BodyFatImpression.very_visible,
        perceived_muscle_mass=PerceivedMuscleMass.well_above_average,
        experience_level=ExperienceLevel.advanced,
    )
    assert result.muscle_level_confidence <= 0.60


def test_consistent_answers_yield_higher_confidence_than_conflicting_ones():
    consistent = score_self_assessment(
        visible_muscle_separation=MuscleSeparation.very_defined,
        vascularity=Vascularity.high,
        body_fat_impression=BodyFatImpression.very_visible,
        perceived_muscle_mass=PerceivedMuscleMass.well_above_average,
        experience_level=ExperienceLevel.advanced,
    )
    conflicting = score_self_assessment(
        visible_muscle_separation=MuscleSeparation.very_defined,
        vascularity=Vascularity.none,
        body_fat_impression=BodyFatImpression.not_visible,
        perceived_muscle_mass=PerceivedMuscleMass.below_average,
        experience_level=ExperienceLevel.beginner,
    )
    assert consistent.muscle_level_confidence > conflicting.muscle_level_confidence


def test_fat_pct_range_widens_and_shifts_with_lower_visibility():
    lean = score_self_assessment(
        visible_muscle_separation=MuscleSeparation.moderate,
        vascularity=Vascularity.slight,
        body_fat_impression=BodyFatImpression.very_visible,
        perceived_muscle_mass=PerceivedMuscleMass.average,
        experience_level=ExperienceLevel.intermediate,
    )
    heavier = score_self_assessment(
        visible_muscle_separation=MuscleSeparation.moderate,
        vascularity=Vascularity.slight,
        body_fat_impression=BodyFatImpression.not_visible,
        perceived_muscle_mass=PerceivedMuscleMass.average,
        experience_level=ExperienceLevel.intermediate,
    )
    assert lean.fat_pct_high < heavier.fat_pct_low
