from __future__ import annotations

from dataclasses import dataclass

from schemas.common import FitnessGoal


_PROTEIN_G_PER_KG: dict[FitnessGoal, float] = {
    FitnessGoal.weight_loss:       1.8,
    FitnessGoal.muscle_gain:       2.0,
    FitnessGoal.strength_gain:     2.0,
    FitnessGoal.endurance_gain:    1.6,
    FitnessGoal.flexibility_gain:  1.4,
    FitnessGoal.general_fitness:   1.4,
}

_CDC_FLOOR_G_PER_KG  = 0.8
_CDC_CEILING_G_PER_KG = 3.5

_KCAL_PER_G_PROTEIN = 4.0
_KCAL_PER_G_CARB    = 4.0
_KCAL_PER_G_FAT     = 9.0
_FAT_FRACTION       = 0.25


@dataclass(frozen=True)
class MacroResult:
    protein_g_per_kg:      float
    protein_g:             float
    fat_g:                 float
    carbs_g:                float
    calorie_from_protein:  float
    calorie_from_fat:      float
    calorie_from_carbs:    float
    cdc_clamped:           bool
    floor_applied:         bool
    notes:                 str


class ProteinEngine:

    def compute(
        self,
        weight_kg: float,
        fitness_goal: FitnessGoal,
        calorie_target: float,
        capacity_score: float = 1.0,
    ) -> MacroResult:

        base_rate = _PROTEIN_G_PER_KG.get(fitness_goal, 1.4)

        bonus = max(0.0, (capacity_score - 0.5) * 0.20)
        raw_rate = base_rate + bonus

        cdc_clamped  = raw_rate > _CDC_CEILING_G_PER_KG
        floor_applied = raw_rate < _CDC_FLOOR_G_PER_KG
        final_rate = max(_CDC_FLOOR_G_PER_KG, min(raw_rate, _CDC_CEILING_G_PER_KG))

        protein_g = round(weight_kg * final_rate, 1)

        fat_kcal = calorie_target * _FAT_FRACTION
        fat_g = round(fat_kcal / _KCAL_PER_G_FAT, 1)

        protein_kcal = protein_g * _KCAL_PER_G_PROTEIN
        carb_kcal    = max(0.0, calorie_target - protein_kcal - fat_kcal)
        carbs_g      = round(carb_kcal / _KCAL_PER_G_CARB, 1)

        carb_kcal_final = carbs_g * _KCAL_PER_G_CARB

        parts = [
            f"Goal: {fitness_goal.value.replace('_', ' ')}",
            f"base {base_rate:.1f} g/kg + capacity bonus {bonus:.2f} g/kg = {final_rate:.2f} g/kg.",
        ]
        if cdc_clamped:
            parts.append(
                f"Rate clamped from {raw_rate:.2f} to CDC ceiling {_CDC_CEILING_G_PER_KG} g/kg."
            )
        if floor_applied:
            parts.append(
                f"Rate raised to CDC floor {_CDC_FLOOR_G_PER_KG} g/kg."
            )

        return MacroResult(
            protein_g_per_kg=round(final_rate, 3),
            protein_g=protein_g,
            fat_g=fat_g,
            carbs_g=carbs_g,
            calorie_from_protein=round(protein_kcal, 1),
            calorie_from_fat=round(fat_kcal, 1),
            calorie_from_carbs=round(carb_kcal_final, 1),
            cdc_clamped=cdc_clamped,
            floor_applied=floor_applied,
            notes=" ".join(parts),
        )

    @staticmethod
    def is_within_cdc_range(protein_g: float, weight_kg: float) -> bool:
        rate = protein_g / max(weight_kg, 1.0)
        return _CDC_FLOOR_G_PER_KG <= rate <= _CDC_CEILING_G_PER_KG


protein_engine = ProteinEngine()
