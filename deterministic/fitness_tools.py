# deterministic/fitness_tools.py
import re
from typing import Optional
from .registry import register_handler

def epley_1rm(weight: float, reps: int) -> float:
    return weight * (1 + reps / 30.0)

def reverse_epley(target_1rm: float, reps: int) -> float:
    return target_1rm / (1 + reps / 30.0)

# Additional deterministic fitness tools

def reps_for_target_1rm(target, weight):
    """
    Solve for reps needed for a given weight to estimate target 1RM.
    """
    if weight <= 0:
        return None
    # weight * (1 + r/30) = target
    r = 30 * ((target / weight) - 1)
    return max(0, r)


def percent_of_max(one_rm, percent):
    return round(one_rm * percent, 1)

@register_handler(priority=10)
def handle_bench_1rm(text: str) -> Optional[str]:
    lower = text.lower()
    if "bench" not in lower:
        return None
    if not any(k in lower for k in ["1rm", "1 rm", "one rep", "1 rep", "rep max", "max rep"]):
        return None

    units = "lbs"

    forward = re.search(r"bench\s+(\d+(\.\d+)?)\s*(lbs|lb|kg)?\s*for\s*(\d+)\s*reps?", lower)
    if forward:
        weight = float(forward.group(1))
        reps = int(forward.group(4))
        one_rm = epley_1rm(weight, reps)
        return (
            f"Using the Epley formula, your estimated 1RM is about "
            f"**{one_rm:.1f} {units}** from {weight:.0f} {units} × {reps} reps."
        )

    nums = re.findall(r"\d+(\.\d+)?", lower)
    if len(nums) >= 2 and "for" in lower and "reps" in lower:
        target_1rm = float(nums[0])
        reps = int(float(nums[1]))
        weight = reverse_epley(target_1rm, reps)
        return (
            f"To target a **{target_1rm:.0f} {units}** 1RM at **{reps} reps**, "
            f"you'd want to hit around **{weight:.1f} {units}** for {reps} reps using the Epley formula."
        )

    return (
        "For 1RM bench calculations, use Epley:\n"
        "**1RM = weight × (1 + reps/30)**.\n"
        "Example: `I bench 200 for 5 reps` or `I want 300 1rm for 8 reps`."
    )

# ==========================================================
# PHASE 5 — FITNESS TOOLS V2
# ==========================================================

# Accurate 1RM via explicit command ------------------------
@register_handler(priority=55)
def handle_1rm(text: str) -> Optional[str]:
    """
    1rm 200 x 5
    """
    lower = text.lower()
    if not lower.startswith("1rm"):
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 2:
        return "Usage: 1rm <weight> x <reps>"

    weight = float(nums[0])
    reps = float(nums[1])
    est = epley_1rm(weight, reps)
    return f"**Estimated 1RM = {est:.0f} lbs**"

# Reverse 1RM ---------------------------------------------
@register_handler(priority=56)
def handle_reverse_1rm(text: str) -> Optional[str]:
    """
    reverse_1rm 315 5
    """
    lower = text.lower()
    if "reverse_1rm" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 2:
        return "Usage: reverse_1rm <1rm> <reps>"

    one_rm = float(nums[0])
    reps = float(nums[1])
    weight = reverse_epley(one_rm, reps)

    return (
        f"To hit a **{one_rm:.0f} lb 1RM**, you need:\n"
        f"- **{weight:.0f} lbs for {reps:.0f} reps**"
    )

# Strength standards --------------------------------------
@register_handler(priority=57)
def handle_strength_level(text: str) -> Optional[str]:
    """
    strength_level bench 200 195
    """
    lower = text.lower()
    if "strength_level" not in lower:
        return None

    tokens = text.split()
    if len(tokens) < 4:
        return "Usage: strength_level <lift> <weight> <bodyweight>"

    lift = tokens[1].lower()
    lift_weight = float(tokens[2])
    bw = float(tokens[3])
    if bw <= 0:
        return "Bodyweight must be positive."

    ratio = lift_weight / bw
    standards = {
        "bench": (0.9, 1.2, 1.5),
        "squat": (1.2, 1.6, 2.0),
        "deadlift": (1.5, 2.0, 2.5),
    }
    if lift not in standards:
        return "Lift must be bench, squat, or deadlift."

    novice, intermediate, advanced = standards[lift]
    if ratio < novice:
        level = "Beginner"
    elif ratio < intermediate:
        level = "Novice"
    elif ratio < advanced:
        level = "Intermediate"
    else:
        level = "Advanced"

    return (
        f"{lift.capitalize()} strength rating:\n"
        f"- Lift: {lift_weight:.0f} lbs\n"
        f"- Bodyweight: {bw:.0f} lbs\n"
        f"- Ratio: {ratio:.2f}\n\n"
        f"→ **{level} level**"
    )

# Warmup calculator ---------------------------------------
@register_handler(priority=58)
def handle_warmup(text: str) -> Optional[str]:
    """
    warmup 315
    """
    lower = text.lower()
    if "warmup" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if not nums:
        return "Usage: warmup <working_set_weight>"

    working = float(nums[0])
    return (
        f"Warm-up sets for **{working:.0f} lbs**:\n"
        f"- 40% → {working * 0.40:.0f} lbs\n"
        f"- 60% → {working * 0.60:.0f} lbs\n"
        f"- 75% → {working * 0.75:.0f} lbs\n"
        f"- 90% → {working * 0.90:.0f} lbs"
    )

