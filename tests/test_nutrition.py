from godbot.deterministic.nutrition_tools import (
    calculate_macros,
    meal_plan_7_day,
    grocery_list_from_plan,
)


def test_macro_calc():
    macros = calculate_macros(2500, "maintain")
    assert macros["calories"] == 2500
    assert macros["protein_g"] > 0


def test_meal_plan():
    macros = calculate_macros(2400, "cut")
    plan = meal_plan_7_day(macros)
    assert len(plan) == 7


def test_grocery_list():
    macros = calculate_macros(2400, "bulk")
    plan = meal_plan_7_day(macros)
    groceries = grocery_list_from_plan(plan)
    assert groceries["chicken_g"] > 0

