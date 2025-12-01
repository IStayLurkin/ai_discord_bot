import math

from godbot.deterministic.finance_tools import (
    coast_fi,
    lean_fi_required,
    safe_withdrawal,
    millionaire_timeline,
    fi_age_projection,
)


def test_coast_fi_basic():
    res = coast_fi(30, 60, 100000, 30000)
    assert "projected_nw" in res
    assert res["projected_nw"] > 0


def test_lean_fi():
    assert lean_fi_required(40000) == 1_000_000


def test_safe_withdrawal():
    annual, monthly = safe_withdrawal(100000)
    assert annual == 4000.00
    assert round(monthly, 2) == round(4000 / 12, 2)


def test_millionaire_timeline():
    res = millionaire_timeline(10000, 500, 0.07, 0.02)
    assert res["years_until_millionaire"] > 0
    assert res["final_nw"] > 10000


def test_fi_age_projection():
    res = fi_age_projection(30, 10000, 6000, 0.07, 1_000_000)
    assert res["fi_age"] >= 30

