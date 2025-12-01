import math

from deterministic.finance_tools import (
    years_to_target,
    required_nest_egg,
    coast_fi_target,
    lean_fi_target,
    inflation_adjusted_target,
    summarize_fi_scenarios,
)


def test_required_nest_egg_basic():
    # 40k/year at 4% -> 1,000,000
    assert required_nest_egg(40_000, 0.04) == 1_000_000


def test_years_to_target_zero_return():
    # 0% return, 1000/month to reach 100k
    years = years_to_target(
        current_balance=0.0,
        monthly_contrib=1000.0,
        annual_return=0.0,
        target=100_000.0,
    )
    # 100k / 1000 = 100 months ≈ 8.33 years
    assert math.isclose(years, 100 / 12, rel_tol=1e-3)


def test_coast_fi_target_reasonable_range():
    # Simple sanity: Coast FI should be far less than FIRE number
    current_age = 30
    retire_age = 60
    desired_spend = 40_000
    fire_number = required_nest_egg(desired_spend, 0.04)
    coast_now = coast_fi_target(
        current_age=current_age,
        retire_age=retire_age,
        desired_annual_spend=desired_spend,
        annual_return=0.07,
        safe_withdrawal_rate=0.04,
    )
    assert coast_now > 0
    assert coast_now < fire_number


def test_lean_fi_target_less_than_fire():
    fire_number = required_nest_egg(40_000, 0.04)
    lean_number = lean_fi_target(25_000, 0.04)
    assert lean_number < fire_number
    assert lean_number == 25_000 / 0.04


def test_inflation_adjusted_target_grows():
    today = 1_000_000
    future = inflation_adjusted_target(today, years=20, inflation_rate=0.02)
    assert future > today


def test_summarize_fi_scenarios_contains_key_phrases():
    summary = summarize_fi_scenarios(
        current_age=31,
        retire_age=55,
        current_balance=50_000,
        monthly_contrib=2_000,
        desired_annual_spend=35_000,
        lean_annual_spend=24_000,
        annual_return=0.07,
        safe_withdrawal_rate=0.04,
        inflation_rate=0.02,
    )
    # Just check that key labels exist; numbers may change with tweaks
    assert "FIRE number (today): $" in summary
    assert "Coast FI balance needed *now*:" in summary
    assert "Estimated years to reach FIRE with current plan:" in summary
    assert "Lean FI target (today): $" in summary
