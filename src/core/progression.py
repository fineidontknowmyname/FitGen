from copy import deepcopy
from typing import List
from schemas.plan import WeeklySchedule, WorkoutSession, WorkoutExercise, WorkoutSet
from schemas.content import Exercise

class ProgressionEngine:
    def apply_progression(self, base_week: WeeklySchedule, total_weeks: int, capacity_score: float) -> List[WeeklySchedule]:
        full_plan = []

        for week_num in range(1, total_weeks + 1):
            current_week = deepcopy(base_week)
            current_week.week_number = week_num

            volume_multiplier = 1.0 + ((week_num - 1) * 0.1)
            intensity_scalar = capacity_score

            for session in current_week.sessions:
                for workout_exercise in session.exercises:
                    for wset in workout_exercise.sets:
                        wset.reps = int(wset.reps * volume_multiplier)

                        if wset.weight_kg > 0:
                            progressive_overload = (week_num - 1) * 2.5
                            wset.weight_kg = (wset.weight_kg * intensity_scalar) + progressive_overload

            full_plan.append(current_week)

        return full_plan

progression_engine = ProgressionEngine()
