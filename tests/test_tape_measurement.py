import pytest

from core.tape_measurement import navy_body_fat_pct, navy_body_fat_range


def test_navy_male_known_value():
    pct = navy_body_fat_pct(neck_cm=38.0, waist_cm=85.0, height_cm=178.0, gender="male")
    assert 8.0 < pct < 20.0


def test_navy_female_known_value():
    pct = navy_body_fat_pct(
        neck_cm=32.0, waist_cm=75.0, height_cm=165.0, gender="female", hip_cm=95.0
    )
    assert 15.0 < pct < 35.0


def test_navy_male_waist_not_greater_than_neck_raises():
    with pytest.raises(ValueError):
        navy_body_fat_pct(neck_cm=40.0, waist_cm=38.0, height_cm=178.0, gender="male")


def test_navy_female_missing_hip_raises():
    with pytest.raises(ValueError):
        navy_body_fat_pct(neck_cm=32.0, waist_cm=75.0, height_cm=165.0, gender="female")


def test_navy_invalid_gender_raises():
    with pytest.raises(ValueError):
        navy_body_fat_pct(neck_cm=38.0, waist_cm=85.0, height_cm=178.0, gender="other")


def test_navy_result_is_clamped_to_sane_range():
    pct = navy_body_fat_pct(neck_cm=45.0, waist_cm=46.0, height_cm=250.0, gender="male")
    assert 3.0 <= pct <= 50.0


def test_navy_range_brackets_the_point_estimate():
    low, high = navy_body_fat_range(neck_cm=38.0, waist_cm=85.0, height_cm=178.0, gender="male")
    point = navy_body_fat_pct(neck_cm=38.0, waist_cm=85.0, height_cm=178.0, gender="male")
    assert low <= point <= high
    assert low < high
