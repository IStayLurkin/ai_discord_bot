# Nutrition & Fitness deterministic module
import re
import math
from typing import Optional
from .registry import register_handler


# ==========================================================
# PURE MATH HELPERS (No Discord/LLM dependencies)
# ==========================================================

# -------------------------------
# 1. TDEE (Total Daily Energy Expenditure)
# -------------------------------

def bmr_mifflin_st_jeor(weight_kg, height_cm, age, sex):
    """
    Mifflin-St Jeor BMR:
    male:   10w + 6.25h - 5a + 5
    female: 10w + 6.25h - 5a - 161
    """
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex.lower().startswith("m") else -161)


def tdee(bmr, activity_level):
    """
    activity_level: one of:
    sedentary, light, moderate, heavy, athlete
    """
    factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "heavy": 1.725,
        "athlete": 1.9,
    }
    return bmr * factors.get(activity_level, 1.2)


# -------------------------------
# 2. Macro breakdown
# -------------------------------

def macro_split(calories, protein_ratio=0.30, fat_ratio=0.25, carb_ratio=0.45):
    """
    Returns grams of protein, fat, carbs for given calorie split.
    """
    p_cal = calories * protein_ratio
    f_cal = calories * fat_ratio
    c_cal = calories * carb_ratio

    protein_g = p_cal / 4
    fat_g = f_cal / 9
    carbs_g = c_cal / 4

    return {
        "protein_g": round(protein_g),
        "fat_g": round(fat_g),
        "carbs_g": round(carbs_g),
    }


# -------------------------------
# 3. Goal-specific calorie targets
# -------------------------------

def calorie_targets(tdee_value):
    """
    Classic 3-phase plan:
    - Cut:     TDEE - 300 to -500
    - Maintain: TDEE
    - Bulk:    TDEE + 250 to +400
    """
    return {
        "cut_low": round(tdee_value - 500),
        "cut_high": round(tdee_value - 300),
        "maintain": round(tdee_value),
        "bulk_low": round(tdee_value + 250),
        "bulk_high": round(tdee_value + 400),
    }


# -------------------------------
# 4. Strength Percentiles (bench/squat/deadlift)
# -------------------------------

# Approx reference standards (intermediate lifter ~50th percentile)
STRENGTH_TABLE = {
    "bench": {
        "novice": 0.8,
        "intermediate": 1.0,
        "advanced": 1.4,
        "elite": 1.8,
    },
    "squat": {
        "novice": 1.0,
        "intermediate": 1.5,
        "advanced": 2.0,
        "elite": 2.5,
    },
    "deadlift": {
        "novice": 1.2,
        "intermediate": 1.8,
        "advanced": 2.3,
        "elite": 2.8,
    },
}


def strength_level(lift_type, one_rm, bodyweight):
    """
    Returns novice / intermediate / advanced / elite
    based on 1RM / bodyweight ratio.
    """
    ratio = one_rm / bodyweight
    table = STRENGTH_TABLE.get(lift_type.lower(), {})

    best_cat = "untrained"
    for cat, req in table.items():
        if ratio >= req:
            best_cat = cat

    return best_cat, ratio


# -------------------------------
# 5. Training Block Generator
# -------------------------------

def create_training_block(style="PPL"):
    """
    Deterministic training templates.
    """
    if style.upper() == "PPL":
        return {
            "Push": ["Bench", "Shoulder Press", "Triceps", "Incline DB", "Lateral Raises"],
            "Pull": ["Deadlift", "Rows", "Pulldowns", "Biceps", "Rear Delt"],
            "Legs": ["Squat", "Leg Press", "Ham Curls", "Calves", "Abs"],
        }

    if style.upper() == "UL":
        return {
            "Upper": ["Bench", "Rows", "Shoulder Press", "Pulldowns", "Biceps/Triceps"],
            "Lower": ["Squat", "Deadlift", "Leg Press", "Ham Curls", "Calves"],
        }

    if style.upper() == "SH":
        return {
            "Strength": ["Bench 3x5", "Squat 3x5", "Deadlift 1x5"],
            "Hypertrophy": ["Incline DB", "Leg Press", "Rows", "Lateral Raises", "Curls"],
        }

    return {"error": "Unknown training style"}


# ==========================================================
# HANDLERS (Discord message pattern matching)
# ==========================================================

# ============================
# BMI
# ============================
@register_handler(priority=79)
def handle_bmi(text: str) -> Optional[str]:
    lower = text.lower()
    if "bmi" not in lower:
        return None

    metric = re.search(r"bmi.*?(\d+(\.\d+)?)\s*(kg|kilograms).*(\d+(\.\d+)?)\s*(cm|centimeters)", lower)
    if metric:
        weight_kg = float(metric.group(1))
        height_cm = float(metric.group(4))
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m ** 2)
        return f"With **{weight_kg:.1f} kg** and **{height_cm:.0f} cm**, BMI ≈ **{bmi:.1f}**."

    imperial = re.search(r"bmi.*?(\d+(\.\d+)?)\s*(lbs|lb|pounds).*(\d+)[' ]\s*(\d+)", lower)
    if imperial:
        weight_lbs = float(imperial.group(1))
        feet = int(imperial.group(4))
        inches = int(imperial.group(5))
        total_inches = feet * 12 + inches
        height_m = total_inches * 0.0254
        weight_kg = weight_lbs * 0.45359237
        bmi = weight_kg / (height_m ** 2)
        return (
            f"With **{weight_lbs:.1f} lbs** at **{feet}'{inches}\"**, "
            f"BMI ≈ **{bmi:.1f}** (standard BMI formula)."
        )

    return (
        "To calculate BMI, use:\n"
        "- `bmi 88 kg 180 cm`\n"
        "- `bmi 195 lbs 6'3`"
    )

# ==========================================================
# PHASE 5 — NUTRITION TOOLS V2
# ==========================================================

# TDEE -----------------------------------------------------
@register_handler(priority=80)
def handle_tdee(text: str) -> Optional[str]:
    """
    tdee <weight_lbs> <height_ft> <height_in> <age> <male/female> <activity>
    """
    lower = text.lower()
    if "tdee" not in lower:
        return None

    tokens = text.split()
    if len(tokens) < 7:
        return "Usage: tdee <weight_lbs> <height_ft> <height_in> <age> <male/female> <activity>"

    try:
        weight = float(tokens[1])
        ft = float(tokens[2])
        inch = float(tokens[3])
        age = float(tokens[4])
        sex = tokens[5].lower()
        activity = tokens[6].lower()
    except ValueError:
        return "Invalid TDEE format."

    kg = weight * 0.453592
    cm = ((ft * 12) + inch) * 2.54

    if sex == "male":
        bmr = 10 * kg + 6.25 * cm - 5 * age + 5
    else:
        bmr = 10 * kg + 6.25 * cm - 5 * age - 161

    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "athlete": 1.9,
    }
    mult = multipliers.get(activity, 1.55)
    tdee = bmr * mult

    return (
        f"**TDEE result:**\n"
        f"- Weight: {weight:.0f} lbs\n"
        f"- Height: {int(ft)}' {int(inch)}\"\n"
        f"- Age: {age:.0f}\n"
        f"- Sex: {sex.capitalize()}\n"
        f"- Activity: {activity.capitalize()}\n\n"
        f"→ **TDEE = {tdee:,.0f} calories/day**"
    )

# Athletic macros ------------------------------------------
@register_handler(priority=81)
def handle_macros(text: str) -> Optional[str]:
    """
    macros <weight_lbs> <calories>
    """
    lower = text.lower()
    if "macros" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 2:
        return "Usage: macros <weight_lbs> <calories>"

    weight = float(nums[0])
    calories = float(nums[1])

    protein_g = weight * 0.8
    fat_g = weight * 0.3
    protein_cals = protein_g * 4
    fat_cals = fat_g * 9
    carbs_g = max(calories - protein_cals - fat_cals, 0) / 4

    return (
        f"**Macro breakdown:**\n"
        f"- Calories: **{calories:,.0f}**\n"
        f"- Protein: **{protein_g:.0f}g**\n"
        f"- Fat: **{fat_g:.0f}g**\n"
        f"- Carbs: **{carbs_g:.0f}g**"
    )

# Protein ranges -------------------------------------------
@register_handler(priority=82)
def handle_protein(text: str) -> Optional[str]:
    """
    protein <weight_lbs>
    """
    if not text.lower().startswith("protein"):
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if not nums:
        return "Usage: protein <weight_lbs>"

    weight = float(nums[0])
    low = weight * 0.6
    med = weight * 0.8
    high = weight * 1.0

    return (
        f"**Protein targets:**\n"
        f"- Low: **{low:.0f}g**\n"
        f"- Moderate: **{med:.0f}g**\n"
        f"- High: **{high:.0f}g**"
    )

# Bulk/Cut calories ----------------------------------------
@register_handler(priority=83)
def handle_bulk_cut_calories(text: str) -> Optional[str]:
    """
    bulk_cut <tdee> <cut/bulk>
    """
    lower = text.lower()
    if "bulk_cut" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if not nums:
        return "Usage: bulk_cut <tdee> <cut/bulk>"

    tdee = float(nums[0])
    goal = "cut" if "cut" in lower else "bulk"
    cals = tdee - 400 if goal == "cut" else tdee + 300

    return f"**Suggested calories for {goal}: {cals:.0f} cals/day**"

# Weight timeline ------------------------------------------
@register_handler(priority=84)
def handle_weight_timeline(text: str) -> Optional[str]:
    """
    weight_timeline <daily_deficit> <lbs_to_lose>
    """
    lower = text.lower()
    if "weight_timeline" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 2:
        return "Usage: weight_timeline <deficit> <lbs_to_lose>"

    deficit = float(nums[0])
    goal = float(nums[1])
    if deficit <= 0:
        return "Calorie deficit must be positive."

    days = goal * 3500 / deficit
    weeks = days / 7

    return (
        f"**Weight change timeline:**\n"
        f"- Deficit: {deficit:.0f} cals/day\n"
        f"- Goal: {goal:.1f} lbs\n\n"
        f"→ Estimated time: **{weeks:.1f} weeks**"
    )

# ============================
# CUT / BULK MACROS (LEGACY PRESETS)
# ============================
@register_handler(priority=86)
def handle_cut_bulk_macros(text: str) -> Optional[str]:
    """
    cut/bulk macros with presets
    """
    lower = text.lower()
    if "cut" not in lower and "bulk" not in lower:
        return None

    if not any(k in lower for k in ["macro", "calorie", "kcal", "cals"]):
        return None

    match = re.search(
        r"(cut|bulk).*?(\d+(\.\d+)?)\s*(lbs|lb|pounds|kg|kilograms)?.*?(\d+(\.\d+)?)\s*(cal|cals|kcal|kcals|calories)?",
        lower,
    )
    if not match:
        return "Usage: cut/bulk macros <weight> <calories>"

    mode = match.group(1)
    weight_val = float(match.group(2))
    unit = match.group(4) or "lbs"
    calories = float(match.group(5))

    weight_lbs = weight_val / 0.45359237 if unit.startswith("kg") else weight_val
    if mode == "cut":
        label = "Cut"
        protein_g = weight_lbs * 1.1
        fat_ratio = 0.20
    else:
        label = "Bulk"
        protein_g = weight_lbs * 0.8
        fat_ratio = 0.30

    fat_cals = calories * fat_ratio
    fat_g = fat_cals / 9
    carbs_g = max(calories - (protein_g * 4 + fat_cals), 0) / 4

    return (
        f"**{label} macros preset** for ~{weight_lbs:.0f} lbs at **{calories:.0f} kcal**:\n"
        f"- Protein: **{protein_g:.0f} g**\n"
        f"- Fat: **{fat_g:.0f} g** (~{fat_ratio*100:.0f}% of calories)\n"
        f"- Carbs: **{carbs_g:.0f} g**"
    )

# ============================
# GENERIC MACROS (NO CUT/BULK LABEL)
# ============================
@register_handler(priority=87)
def handle_calories_macros(text: str) -> Optional[str]:
    lower = text.lower()
    if "macros" not in lower and "macro" not in lower and "calories" not in lower:
        return None

    if "cut" in lower or "bulk" in lower:
        return None

    m = re.search(
        r"macros\s+(\d+(\.\d+)?)\s*(lbs|lb|pounds|kg|kilograms)?.*?(\d+(\.\d+)?)\s*(cal|cals|kcal|kcals|calories)?",
        lower,
    )
    if not m:
        return "Usage: macros <weight> <calories>"

    weight_val = float(m.group(1))
    unit = m.group(3) or "lbs"
    calories = float(m.group(4))

    weight_lbs = weight_val / 0.45359237 if unit.startswith("kg") else weight_val
    protein_g = weight_lbs * 1.0
    fat_cals = calories * 0.25
    fat_g = fat_cals / 9
    carbs_g = max(calories - (protein_g * 4 + fat_cals), 0) / 4

    return (
        f"For **~{weight_lbs:.0f} lbs** at **{calories:.0f} kcal**:\n"
        f"- Protein: **{protein_g:.0f} g** (~1 g/lb)\n"
        f"- Fat: **{fat_g:.0f} g** (~25% of calories)\n"
        f"- Carbs: **{carbs_g:.0f} g** (rest of calories)"
    )