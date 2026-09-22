from __future__ import annotations

import math

_MIN_FAT_PCT = 3.0
_MAX_FAT_PCT = 50.0
_ERROR_MARGIN_FRACTION = 0.035


def navy_body_fat_pct(
    neck_cm: float,
    waist_cm: float,
    height_cm: float,
    gender: str,
    hip_cm: float | None = None,
) -> float:
    gender = gender.lower()

    if gender == "male":
        if waist_cm <= neck_cm:
            raise ValueError("waist_cm must be greater than neck_cm for the Navy method (male).")
        val = (
            495
            / (
                1.0324
                - 0.19077 * math.log10(waist_cm - neck_cm)
                + 0.15456 * math.log10(height_cm)
            )
            - 450
        )
    elif gender == "female":
        if hip_cm is None:
            raise ValueError("hip_cm is required for the Navy method (female).")
        combined = waist_cm + hip_cm - neck_cm
        if combined <= 0:
            raise ValueError("waist_cm + hip_cm must be greater than neck_cm for the Navy method (female).")
        val = (
            495
            / (
                1.29579
                - 0.35004 * math.log10(combined)
                + 0.22100 * math.log10(height_cm)
            )
            - 450
        )
    else:
        raise ValueError("gender must be 'male' or 'female'.")

    return max(_MIN_FAT_PCT, min(_MAX_FAT_PCT, val))


def navy_body_fat_range(
    neck_cm: float,
    waist_cm: float,
    height_cm: float,
    gender: str,
    hip_cm: float | None = None,
) -> tuple[float, float]:
    point_estimate = navy_body_fat_pct(neck_cm, waist_cm, height_cm, gender, hip_cm)
    spread = max(0.5, point_estimate * _ERROR_MARGIN_FRACTION)
    low = max(_MIN_FAT_PCT, round(point_estimate - spread, 1))
    high = min(_MAX_FAT_PCT, round(point_estimate + spread, 1))
    return low, high
