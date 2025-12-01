"""
Deterministic Fitness Tools (Phase 5)
Pure math + static percentile tables.
No LLM usage.
"""

from __future__ import annotations

from typing import Dict, List


# -----------------------------------------
# Strength Percentile Tables (simplified)
# Values are percentiles for 1RM at given BW
# -----------------------------------------
STRENGTH_TABLES = {
    "bench": {
        150: {100: 20, 135: 50, 185: 80, 225: 95},
        180: {135: 20, 185: 50, 225: 80, 275: 95},
        200: {155: 20, 205: 50, 255: 80, 300: 95},
    },
    "squat": {
        150: {135: 20, 185: 50, 225: 80, 275: 95},
        180: {185: 20, 225: 50, 275: 80, 325: 95},
        200: {205: 20, 275: 50, 325: 80, 375: 95},
    },
    "deadlift": {
        150: {185: 20, 225: 50, 275: 80, 315: 95},
        180: {225: 20, 275: 50, 325: 80, 365: 95},
        200: {245: 20, 315: 50, 365: 80, 405: 95},
    },
}


# -------------------------------------------------------
# Strength Percentile Evaluator
# -------------------------------------------------------
def strength_percentile(lift: str, weight: float, bodyweight: float) -> int:
    """
    Returns approximate percentile for a given lift.
    lift: bench, squat, deadlift
    """
    lift = lift.lower()
    if lift not in STRENGTH_TABLES:
        return 0

    # pick closest BW category
    bw_table = min(STRENGTH_TABLES[lift].keys(), key=lambda x: abs(x - bodyweight))
    table = STRENGTH_TABLES[lift][bw_table]

    # find percentile by comparing thresholds
    best = 0
    for threshold, pct in table.items():
        if weight >= threshold:
            best = pct
    return best


# -------------------------------------------------------
# Training Block Generator (PPL, UL, Hybrid)
# -------------------------------------------------------
TRAINING_BLOCKS = {
    "ppl": [
        "Push: Bench, OHP, Dips",
        "Pull: Rows, Pulldowns, Curls",
        "Legs: Squat, RDL, Lunges",
    ],
    "ul": [
        "Upper: Bench, Rows, OHP, Pull-ups",
        "Lower: Squat, RDL, Leg Press, Calves",
    ],
    "hybrid": [
        "Strength Upper: Bench 5x5, Row 5x5",
        "Strength Lower: Squat 5x5, Deadlift 3x5",
        "Hypertrophy Upper",
        "Hypertrophy Lower",
    ],
}


def generate_training_block(style: str, experience: str) -> Dict[str, List[str]]:
    """
    Returns a deterministic training split.
    """
    style = style.lower()
    if style not in TRAINING_BLOCKS:
        return {"error": "Unknown training style"}

    base = TRAINING_BLOCKS[style]
    multiplier = {"beginner": 1, "intermediate": 1.2, "advanced": 1.5}.get(
        experience.lower(), 1
    )

    return {"split": base, "volume_multiplier": multiplier}


# -------------------------------------------------------
# Volume Recommendation Engine
# -------------------------------------------------------
VOLUME_TABLE = {
    "chest": (10, 20),
    "back": (12, 22),
    "shoulders": (8, 20),
    "legs": (12, 24),
    "arms": (8, 16),
}


def recommended_volume(muscle: str, experience: str) -> Dict[str, float]:
    """
    Returns weekly sets based on typical hypertrophy evidence ranges.
    """
    muscle = muscle.lower()
    if muscle not in VOLUME_TABLE:
        return {"error": "Unknown muscle group"}

    base_min, base_max = VOLUME_TABLE[muscle]
    factor = {"beginner": 0.8, "intermediate": 1.0, "advanced": 1.2}.get(
        experience.lower(), 1.0
    )

    return {
        "min_sets": round(base_min * factor, 1),
        "max_sets": round(base_max * factor, 1),
    }

