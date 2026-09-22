from typing import List
from schemas.content import Exercise
from schemas.common import Injury, Equipment

class SafetyFilterEngine:
    def filter_exercises(self, exercises: List[Exercise], injuries: List[Injury], available_equipment: List[Equipment]) -> List[Exercise]:
        safe_list = []

        for exercise in exercises:

            missing_equipment = [
                eq for eq in exercise.equipment_needed
                if eq not in available_equipment and eq != Equipment.bodyweight
            ]

            if missing_equipment:
                continue

            is_unsafe = False
            for muscle in exercise.muscles_worked:
                muscle_key = muscle.lower().strip()
                if any(inj.value == muscle_key for inj in injuries):
                    is_unsafe = True
                    break

            if is_unsafe:
                continue

            safe_list.append(exercise)

        return safe_list

safety_engine = SafetyFilterEngine()
