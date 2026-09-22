from typing import Optional
from schemas.user import UserMetrics, StrengthMetrics, PhysicalActivity, Gender
from schemas.vision import BodyComposition, SWRCategory
from schemas.common import MuscleLevel


_ACTIVITY_BONUS: list[tuple[float, float]] = [
    (0.0,  0.00),
    (0.5,  0.03),
    (1.0,  0.06),
    (1.5,  0.09),
    (2.0,  0.12),
]

_MUSCLE_BONUS: dict[MuscleLevel, float] = {
    MuscleLevel.low:       -0.05,
    MuscleLevel.moderate:   0.00,
    MuscleLevel.high:       0.07,
    MuscleLevel.very_high:  0.12,
}


class CapacityEngine:

    def calculate_score(
        self,
        user_metrics: UserMetrics,
        strength_metrics: StrengthMetrics,
        physical_activity: Optional[PhysicalActivity] = None,
        body_composition: Optional[BodyComposition] = None,
    ) -> float:
        raw_score = self._strength_score(user_metrics, strength_metrics)

        if physical_activity is not None:
            raw_score += self._activity_bonus(
                physical_activity.physical_activity_hours_per_day
            )

        raw_score += self._bmi_adjustment(user_metrics)

        if body_composition is not None:
            raw_score += self._muscle_bonus(body_composition)

        if body_composition is not None:
            raw_score += self._swr_adjustment(body_composition)

        return round(max(0.50, min(raw_score, 1.50)), 4)

    def _strength_score(
        self,
        user_metrics: UserMetrics,
        strength_metrics: StrengthMetrics,
    ) -> float:
        pushup_std = 20.0 if user_metrics.gender == Gender.male else 10.0
        squat_std  = 30.0

        if user_metrics.age > 40:
            pushup_std *= 0.8
            squat_std  *= 0.8

        pushup_ratio = strength_metrics.pushup_count / max(pushup_std, 1.0)
        squat_ratio  = strength_metrics.squat_count  / max(squat_std,  1.0)

        run_std = 6.0
        if strength_metrics.run_time_min and strength_metrics.run_time_min > 0:
            cardio_ratio = run_std / strength_metrics.run_time_min
        else:
            cardio_ratio = 1.0

        return (pushup_ratio * 0.40) + (squat_ratio * 0.30) + (cardio_ratio * 0.30)

    def _activity_bonus(self, hours_per_day: float) -> float:
        bonus = 0.0
        for threshold, value in reversed(_ACTIVITY_BONUS):
            if hours_per_day >= threshold:
                bonus = value
                break
        return bonus

    def _bmi_adjustment(self, user_metrics: UserMetrics) -> float:
        height_m = user_metrics.height_cm / 100.0
        bmi = user_metrics.weight_kg / (height_m ** 2)

        if bmi < 17.0:
            return -0.10
        elif bmi < 18.5:
            return -0.05
        elif bmi < 30.0:
            return 0.00
        elif bmi < 35.0:
            return -0.05
        else:
            return -0.10

    def _muscle_bonus(self, body_composition: BodyComposition) -> float:
        if not body_composition.is_valid_person:
            return 0.0
        if body_composition.confidence < 0.40:
            return 0.0
        if body_composition.muscle_level is None:
            return 0.0

        return _MUSCLE_BONUS.get(body_composition.muscle_level, 0.0)

    def _swr_adjustment(self, body_composition: BodyComposition) -> float:
        if not body_composition.is_valid_person:
            return 0.0
        cat = body_composition.swr_category
        if cat == SWRCategory.OVERFAT:
            return -0.05
        if cat == SWRCategory.ATHLETIC:
            return 0.05
        return 0.0

    @staticmethod
    def swr_weight_multiplier(body_composition: Optional[BodyComposition]) -> float:
        if body_composition is None:
            return 1.0
        if body_composition.swr_category == SWRCategory.ATHLETIC:
            return 1.1
        return 1.0


capacity_engine = CapacityEngine()
