"""
Deterministic Nutrition Tools (Phase 5)
Pure math macros, TDEE-based plans, no LLM logic here.
"""

from __future__ import annotations

from typing import Dict, List

# Phase 11.1 logging
from godbot.core.logging import get_logger

log = get_logger(__name__)


# ------------------------------------------------
# Deterministic Macro Calculator
# ------------------------------------------------
def calculate_macros(tdee: int, goal: str) -> Dict[str, float]:
    """
    goal: cut / maintain / bulk
    """
    goal = goal.lower()
    if goal == "cut":
        calories = tdee - 300
    elif goal == "bulk":
        calories = tdee + 300
    else:
        calories = tdee

    # macros: 40/30/30 split
    protein = calories * 0.30 / 4
    carbs = calories * 0.40 / 4
    fats = calories * 0.30 / 9

    return {
        "calories": round(calories),
        "protein_g": round(protein),
        "carbs_g": round(carbs),
        "fats_g": round(fats),
    }


# ------------------------------------------------
# Static food database (very small deterministic set)
# ------------------------------------------------
FOOD_DB = {
    "chicken": {"cal": 165, "p": 31, "c": 0, "f": 4},
    "rice": {"cal": 206, "p": 4, "c": 45, "f": 0},
    "eggs": {"cal": 72, "p": 6, "c": 0, "f": 5},
    "oats": {"cal": 150, "p": 5, "c": 27, "f": 3},
    "banana": {"cal": 100, "p": 1, "c": 27, "f": 0},
}


def parse_ingredient(name: str) -> Dict[str, int]:
    """Return macros from FOOD_DB."""
    name = name.lower()
    return FOOD_DB.get(name, {"cal": 0, "p": 0, "c": 0, "f": 0})


# ------------------------------------------------
# Meal Plan Generator (math only)
# ------------------------------------------------
def meal_plan_7_day(macros: Dict[str, float]) -> List[Dict[str, float]]:
    """
    Deterministic ingredients to match macro targets.
    Chooses fixed foods at scaled quantities.
    """
    target_p = macros["protein_g"]
    target_c = macros["carbs_g"]
    target_f = macros["fats_g"]

    # deterministic fixed ratio meals
    day = {
        "chicken_g": round(target_p / 0.31),
        "rice_g": round(target_c / 0.45),
        "eggs_count": round(target_f / 5),
    }

    return [day for _ in range(7)]


# ------------------------------------------------
# Grocery List Aggregator
# ------------------------------------------------
def grocery_list_from_plan(plan: List[Dict[str, float]]) -> Dict[str, float]:
    """Aggregate all ingredient quantities for 7 days."""
    total = {"chicken_g": 0, "rice_g": 0, "eggs_count": 0}

    for day in plan:
        for key in total.keys():
            total[key] += day.get(key, 0)

    return total

