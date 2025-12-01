import math

from deterministic.nutrition_tools import (
    bmr_mifflin_st_jeor,
    tdee,
    macro_split,
    calorie_targets,
)


def test_bmr_mifflin_male():
    # Example: 80kg, 180cm, 30yo male
    bmr = bmr_mifflin_st_jeor(
        weight_kg=80,
        height_cm=180,
        age=30,
        sex="m",
    )
    # 10*80 + 6.25*180 - 5*30 + 5 = 1780
    assert math.isclose(bmr, 1780, rel_tol=0.01)


def test_tdee_moderate_activity():
    bmr = 1780
    tdee_val = tdee(bmr, "moderate")  # 1.55x
    assert math.isclose(tdee_val, 1780 * 1.55, rel_tol=0.01)


def test_macro_split_default_ratios():
    # 2600 kcal, default ratios
    split = macro_split(2600)
    # rough sanity checks
    assert split["protein_g"] > 150
    assert split["fat_g"] > 50
    assert split["carbs_g"] > 200
    # sum of macro calories should be close to 2600
    total_cals = (
        split["protein_g"] * 4
        + split["fat_g"] * 9
        + split["carbs_g"] * 4
    )
    assert abs(total_cals - 2600) < 150  # allow rounding wiggle room


def test_calorie_targets_cut_maintain_bulk():
    targets = calorie_targets(2700)
    assert targets["cut_low"] < 2700
    assert targets["cut_high"] < 2700
    assert targets["maintain"] == 2700
    assert targets["bulk_low"] > 2700
    assert targets["bulk_high"] > 2700
