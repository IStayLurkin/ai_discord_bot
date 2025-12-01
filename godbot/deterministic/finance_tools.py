"""
Deterministic Finance Tools (Phase 4)
100% pure math, no LLM involvement.
Python 3.10+ compatible.
"""

from __future__ import annotations

import math
from typing import List, Dict, Tuple

# Phase 11.1 logging
from godbot.core.logging import get_logger

log = get_logger(__name__)


# -------------------------
# Coast FI Calculator
# -------------------------
def coast_fi(
    current_age: int,
    fire_age: int,
    current_nw: float,
    annual_spending: float,
    roi: float = 0.07,
) -> Dict[str, float]:
    """
    Determines if the current net worth will grow enough by FIRE age
    without further contributions.

    Returns:
        {
            "projected_nw": float,
            "required_fi_number": float,
            "difference": float,
            "coast_fi": bool
        }
    """
    years = max(fire_age - current_age, 0)
    projected_nw = current_nw * ((1 + roi) ** years)
    required_fi_number = annual_spending * 25
    difference = projected_nw - required_fi_number
    return {
        "projected_nw": projected_nw,
        "required_fi_number": required_fi_number,
        "difference": difference,
        "coast_fi": projected_nw >= required_fi_number,
    }


# -------------------------
# Lean FI Requirement
# -------------------------
def lean_fi_required(annual_spending: float, swr: float = 0.04) -> float:
    """Return minimum FI number using SWR."""
    return annual_spending / swr


# -------------------------
# Drawdown Retirement Simulator
# -------------------------
def retirement_drawdown(
    start_nw: float,
    years: int,
    withdrawal: float,
    roi: float,
    inflation: float,
) -> List[Dict[str, float]]:
    """
    Simulates each year of retirement:
        new_nw = (nw - withdrawal) * (1 + roi)
        withdrawal increases w/ inflation
    """
    nw = start_nw
    wd = withdrawal
    timeline = []

    for year in range(years):
        nw = (nw - wd) * (1 + roi)
        timeline.append({"year": year + 1, "net_worth": nw, "withdrawal": wd})
        wd *= (1 + inflation)
        if nw <= 0:
            break

    return timeline


# -------------------------
# Tax-Adjusted Retirement Model
# -------------------------
def after_tax_retirement_balance(balance: float, tax_rate: float) -> float:
    """Apply withdrawal tax to a retirement balance."""
    return balance * (1 - tax_rate)


# -------------------------
# Inflation-Adjusted Millionaire Timeline
# -------------------------
def millionaire_timeline(
    current_nw: float,
    monthly_contrib: float,
    roi: float,
    inflation: float,
) -> Dict[str, float]:
    """
    Determine how many years until $1M REAL (inflation-adjusted).
    """
    target = 1_000_000
    adjusted_target = target
    nw = current_nw
    years = 0

    while nw < adjusted_target:
        years += 1
        # compound NW
        nw = nw * (1 + roi) + (monthly_contrib * 12)
        # adjust target for inflation
        adjusted_target = adjusted_target * (1 + inflation)
        if years > 120:  # 120 years failsafe
            break

    return {
        "years_until_millionaire": years,
        "final_nw": nw,
        "inflation_adjusted_target": adjusted_target,
    }


# -------------------------
# Safe Monthly Withdrawal
# -------------------------
def safe_withdrawal(nw: float, swr: float = 0.04) -> Tuple[float, float]:
    """Returns (annual, monthly) using the safe withdrawal rate."""
    annual = nw * swr
    monthly = annual / 12
    monthly = round(monthly, 2)
    annual = round(annual, 2)
    return annual, monthly


# -------------------------
# Age-Based FI Projection
# -------------------------
def fi_age_projection(
    current_age: int,
    current_nw: float,
    contrib: float,
    roi: float,
    target: float,
) -> Dict[str, float]:
    """
    Project age when target FI number is reached.
    """
    age = current_age
    nw = current_nw

    while nw < target and age < 120:
        age += 1
        nw = nw * (1 + roi) + contrib * 12

    return {"fi_age": age, "final_nw": nw}

