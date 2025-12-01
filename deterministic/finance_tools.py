# deterministic/finance_tools.py
import re
import math
from typing import Optional
from .registry import register_handler


# ==========================================================
# PURE MATH HELPERS (No Discord/LLM dependencies)
# ==========================================================

def years_to_target(
    current_balance: float,
    monthly_contrib: float,
    annual_return: float,
    target: float,
) -> float:
    """
    Approximate years to reach 'target' given:
    - current_balance
    - monthly_contrib
    - annual_return (e.g. 0.07 for 7%)

    Uses a simple compound interest + annuity formula.
    """
    if annual_return <= 0:
        if monthly_contrib <= 0:
            return math.inf
        months = max(0.0, (target - current_balance) / monthly_contrib)
        return months / 12.0

    r = annual_return / 12.0
    B0 = current_balance
    P = monthly_contrib
    # We solve approximately via iteration (simple, monotonic)
    years = 0.0
    balance = B0
    while balance < target and years < 120:  # hard cap at 120y
        # one year of monthly contributions + compounding
        for _ in range(12):
            balance = balance * (1 + r) + P
        years += 1.0
    return years


def required_nest_egg(
    annual_spend: float,
    safe_withdrawal_rate: float = 0.04,
) -> float:
    """
    Simple FIRE-style target: nest egg = annual_spend / SWR.
    e.g. 40k/year at 4% => 1,000,000
    """
    if safe_withdrawal_rate <= 0:
        return math.inf
    return annual_spend / safe_withdrawal_rate


def coast_fi_target(
    current_age: int,
    retire_age: int,
    desired_annual_spend: float,
    annual_return: float = 0.07,
    safe_withdrawal_rate: float = 0.04,
) -> float:
    """
    Coast FI: amount you need *now* so you can stop contributing entirely,
    let it grow until retire_age, and still hit your FIRE number.

    We compute the FIRE number, then discount it back from retire_age
    using expected return.
    """
    fire_number = required_nest_egg(desired_annual_spend, safe_withdrawal_rate)
    years = max(0, retire_age - current_age)
    return fire_number / ((1 + annual_return) ** years)


def lean_fi_target(
    lean_annual_spend: float,
    safe_withdrawal_rate: float = 0.04,
) -> float:
    """
    Lean FI: lower lifestyle / lower annual spend => smaller FI number.
    Just a variant of the standard FIRE calc.
    """
    return required_nest_egg(lean_annual_spend, safe_withdrawal_rate)


def inflation_adjusted_target(
    today_target: float,
    years: float,
    inflation_rate: float = 0.02,
) -> float:
    """
    Adjust a target for inflation: future_target = today_target * (1 + i)^years
    """
    return today_target * ((1 + inflation_rate) ** years)


def summarize_fi_scenarios(
    current_age: int,
    retire_age: int,
    current_balance: float,
    monthly_contrib: float,
    desired_annual_spend: float,
    lean_annual_spend: Optional[float] = None,
    annual_return: float = 0.07,
    safe_withdrawal_rate: float = 0.04,
    inflation_rate: float = 0.02,
) -> str:
    """
    Returns a human-readable summary string covering:
    - FIRE number
    - Coast FI number
    - Lean FI number (if provided)
    - Years to FIRE from current path
    """
    fire_number_today = required_nest_egg(desired_annual_spend, safe_withdrawal_rate)
    coast_now = coast_fi_target(
        current_age=current_age,
        retire_age=retire_age,
        desired_annual_spend=desired_annual_spend,
        annual_return=annual_return,
        safe_withdrawal_rate=safe_withdrawal_rate,
    )

    years_to_fire = years_to_target(
        current_balance=current_balance,
        monthly_contrib=monthly_contrib,
        annual_return=annual_return,
        target=fire_number_today,
    )

    lean_str = ""
    if lean_annual_spend is not None:
        lean_target = lean_fi_target(lean_annual_spend, safe_withdrawal_rate)
        lean_future = inflation_adjusted_target(lean_target, years_to_fire, inflation_rate)
        lean_str = (
            f"\n\nLean FI target (today): ${lean_target:,.0f}"
            f"\nLean FI target (inflation-adjusted in ~{years_to_fire:.1f}y): ${lean_future:,.0f}"
        )

    fire_future = inflation_adjusted_target(fire_number_today, years_to_fire, inflation_rate)

    return (
        f"FIRE number (today): ${fire_number_today:,.0f}"
        f"\nCoast FI balance needed *now*: ${coast_now:,.0f}"
        f"\nEstimated years to reach FIRE with current plan: {years_to_fire:.1f} years"
        f"\nInflation-adjusted FIRE target in ~{years_to_fire:.1f}y: ${fire_future:,.0f}"
        f"{lean_str}"
    )


# ==========================================================
# HANDLERS (Discord message pattern matching)
# ==========================================================

@register_handler(priority=20)
def handle_millionaire_timeline(text: str) -> Optional[str]:
    """
    'millionaire 90000 3000 7 1000000'
    -> start, monthly, annual%, target (default 1,000,000)
    """
    lower = text.lower()
    if "millionaire" not in lower and "million" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 2:
        return (
            "For a millionaire timeline, use:\n"
            "`millionaire 90000 3000 7 1000000` → start, monthly, annual%, target."
        )

    start = float(nums[0])
    monthly = float(nums[1])
    annual = float(nums[2]) if len(nums) >= 3 else 7.0
    target = float(nums[3]) if len(nums) >= 4 else 1_000_000.0

    if annual <= -100:
        return "Annual return must be greater than -100%."

    r_month = (annual / 100.0) / 12.0
    balance = start
    months = 0
    max_months = 12 * 100

    while balance < target and months < max_months:
        if r_month != 0:
            balance *= (1 + r_month)
        balance += monthly
        months += 1

    if balance < target:
        return (
            f"With **${start:,.0f}** start, **${monthly:,.0f}/mo**, and **{annual:.1f}%/yr**, "
            f"you won't hit **${target:,.0f}** within 100 years."
        )

    years = months // 12
    rem_months = months % 12
    return (
        f"Starting at **${start:,.0f}**, investing **${monthly:,.0f}/month** at **{annual:.1f}%/yr**, "
        f"you'd hit **${target:,.0f}** in about **{years} years {rem_months} months**.\n"
        f"End balance then ≈ **${balance:,.0f}**."
    )

@register_handler(priority=25)
def handle_investment_projection(text: str) -> Optional[str]:
    """
    'invest 90000 3000 7 30'
     -> start, monthly, annual%, years (default 10)
    Triggers on stock/invest/portfolio/etf.
    """
    lower = text.lower()
    if not any(k in lower for k in ["stock", "portfolio", "invest", "investment", "etf", "index fund", "index etf"]):
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 3:
        return (
            "For an investment projection, use:\n"
            "`invest 90000 3000 7 30` → start, monthly, annual%, years."
        )

    start = float(nums[0])
    monthly = float(nums[1])
    annual = float(nums[2])
    years = float(nums[3]) if len(nums) >= 4 else 10.0

    if annual <= -100:
        return "Annual return must be greater than -100%."

    r_month = (annual / 100.0) / 12.0
    balance = start
    months = int(round(years * 12))
    for _ in range(months):
        if r_month != 0:
            balance *= (1 + r_month)
        balance += monthly

    total_contrib = start + monthly * months
    gain = balance - total_contrib

    return (
        f"Starting at **${start:,.0f}** and adding **${monthly:,.0f}/month** at **{annual:.1f}%/yr** "
        f"for **{years:.1f} years**, you'd have about **${balance:,.0f}**.\n"
        f"Total contributions: **${total_contrib:,.0f}**, growth: **${gain:,.0f}**."
    )

@register_handler(priority=30)
def handle_fire_number(text: str) -> Optional[str]:
    """
    'fire 3000'  → default 25x
    'lean fi 2500' → 30x
    'fat fire 6000' → 20x
    """
    lower = text.lower()
    if "fire" not in lower and "lean fi" not in lower and "leanfi" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if not nums:
        return (
            "For FIRE number, use:\n"
            "- `fire 3000`\n"
            "- `lean fi 2500`\n"
            "- `fat fire 6000`"
        )

    monthly_spend = float(nums[0])

    if "lean fi" in lower or "leanfi" in lower:
        multiple = 30.0
        label = "Lean FI"
    elif "fat fire" in lower or "fatfire" in lower:
        multiple = 20.0
        label = "Fat FIRE"
    else:
        multiple = 25.0
        label = "FIRE"

    annual_spend = monthly_spend * 12.0
    target = annual_spend * multiple

    return (
        f"{label} target for **${monthly_spend:,.0f}/mo** spend:\n"
        f"- Annual spend: **${annual_spend:,.0f}/yr**\n"
        f"- Target ≈ **${target:,.0f}** (using {1.0/multiple*100:.2f}% withdrawal)."
    )

@register_handler(priority=35)
def handle_coast_fi(text: str) -> Optional[str]:
    """
    `coast fi number 31 65 3000 7`
     -> current_age, retire_age, monthly_spend, annual_return%
    """
    lower = text.lower()
    if not any(
        key in lower
        for key in ["coast fi number", "coast number", "coast requirement", "coastfi number"]
    ):
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 3:
        return (
            "For Coast FI, use:\n"
            "`coast fi 31 65 3000 7` → current_age, retire_age, monthly_spend, annual_return%."
        )

    current_age = float(nums[0])
    retire_age = float(nums[1])
    monthly_spend = float(nums[2])
    annual_return = float(nums[3]) if len(nums) >= 4 else 7.0

    if retire_age <= current_age:
        return "Retire age must be greater than current age."

    years = retire_age - current_age
    annual_spend = monthly_spend * 12.0
    fire_target = annual_spend * 25.0

    r = annual_return / 100.0
    coast_number = fire_target / ((1 + r) ** years)

    return (
        f"Coast FI:\n"
        f"- Current age **{current_age:.0f}**, retire at **{retire_age:.0f}** → **{years:.0f} years**.\n"
        f"- Target spending: **${monthly_spend:,.0f}/mo** → FIRE ≈ **${fire_target:,.0f}**.\n"
        f"- At **{annual_return:.1f}%/yr**, coast number ≈ **${coast_number:,.0f}** now."
    )

# ==========================================================
#  PHASE 4 — ADVANCED FINANCE TOOLS
# ==========================================================

# ---------------------------
# 1. Coast FI (age when you can stop investing)
# ---------------------------
@register_handler(priority=28)
def handle_coast_fi_age(text: str) -> Optional[str]:
    """
    coast_fi 90000 7 65 1000000
    -> savings, annual%, retire_age, FI target
    """
    lower = text.lower()
    if "coast_fi" not in lower and "coast fi" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 4:
        return "Usage: coast_fi <savings> <annual%> <retire_age> <target_FI>"

    savings = float(nums[0])
    annual = float(nums[1])
    retire_age = float(nums[2])
    target = float(nums[3])

    r = annual / 100.0
    coast_age = None
    for age in range(18, int(retire_age)):
        years = retire_age - age
        fv = savings * ((1 + r) ** years)
        if fv >= target:
            coast_age = age
            break

    if coast_age is None:
        return "You cannot coast to FI with these numbers. Keep investing."

    return (
        f"Coast FI result:\n"
        f"- Current savings: **${savings:,.0f}**\n"
        f"- Annual return: **{annual:.1f}%**\n"
        f"- FI target: **${target:,.0f}** by age **{retire_age:.0f}**\n\n"
        f"→ You can coast starting at **age {coast_age}**."
    )

# ---------------------------
# 2. Lean FI calculator
# ---------------------------
@register_handler(priority=29)
def handle_lean_fi(text: str) -> Optional[str]:
    """
    lean_fi 2500  (monthly expenses)
    """
    lower = text.lower()
    if "lean_fi" not in lower and "lean fi" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if not nums:
        return "Usage: lean_fi <monthly_expenses>"

    monthly = float(nums[0])
    yearly = monthly * 12
    lean_fi = yearly * 25

    return (
        f"Lean FI number:\n"
        f"- Monthly expenses: **${monthly:,.0f}**\n"
        f"- Yearly: **${yearly:,.0f}**\n\n"
        f"→ Lean FI = **${lean_fi:,.0f}**"
    )

# ---------------------------
# 3. Safe spend calculator
# ---------------------------
@register_handler(priority=30)
def handle_safe_spend(text: str) -> Optional[str]:
    """
    safe_spend savings years
    """
    lower = text.lower()
    if "safe_spend" not in lower and "safe spend" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 2:
        return "Usage: safe_spend <savings> <years>"

    savings = float(nums[0])
    years = float(nums[1])
    months = max(years * 12, 1)
    spend = savings / months

    return (
        f"Safe spend plan:\n"
        f"- Savings: **${savings:,.0f}**\n"
        f"- Horizon: **{years:.1f} years**\n\n"
        f"→ Monthly safe spend ≈ **${spend:,.0f}**"
    )

# ---------------------------
# 4. Inflation-adjusted millionaire timeline
# ---------------------------
@register_handler(priority=31)
def handle_inflation_million(text: str) -> Optional[str]:
    """
    infl_million start monthly annual% inflation% target
    Example: infl_million 90000 3000 7 3 1000000
    """
    lower = text.lower()
    if "infl_million" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 5:
        return "Usage: infl_million <start> <monthly> <annual%> <infl%> <target>"

    start, monthly, annual, infl, target = map(float, nums)
    r = annual / 100 / 12
    i = infl / 100 / 12

    balance = start
    inflated_target = target
    months = 0
    max_months = 12 * 100

    while months < max_months:
        inflated_target *= (1 + i)
        balance = balance * (1 + r) + monthly
        months += 1
        if balance >= inflated_target:
            break

    if balance < inflated_target:
        return "You won't reach $1M in today's dollars within 100 years."

    years = months // 12
    rem = months % 12

    return (
        f"Inflation-adjusted millionaire timeline:\n"
        f"- Start **${start:,.0f}**, monthly **${monthly:,.0f}**\n"
        f"- Return **{annual:.1f}%**, inflation **{infl:.1f}%**\n\n"
        f"→ $1M (today's dollars) in **{years} years {rem} months**."
    )

# ---------------------------
# 5. Net worth projection to specific age
# ---------------------------
@register_handler(priority=32)
def handle_networth_age(text: str) -> Optional[str]:
    """
    networth_age start monthly annual% current_age future_age
    """
    lower = text.lower()
    if "networth_age" not in lower and "net worth age" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 5:
        return "Usage: networth_age <start> <monthly> <annual%> <current_age> <future_age>"

    start, monthly, annual, now_age, future_age = map(float, nums)
    months = int((future_age - now_age) * 12)
    if months <= 0:
        return "Future age must be greater than current age."

    r = annual / 100 / 12
    balance = start
    for _ in range(months):
        balance = balance * (1 + r) + monthly

    return f"Net worth at age **{future_age:.0f}** ≈ **${balance:,.0f}**."

# ---------------------------
# 6. Retirement drawdown simulator
# ---------------------------
@register_handler(priority=33)
def handle_drawdown(text: str) -> Optional[str]:
    """
    drawdown savings annual% withdrawal%
    """
    lower = text.lower()
    if "drawdown" not in lower:
        return None

    nums = re.findall(r"\d+(\.\d+)?", text)
    if len(nums) < 3:
        return "Usage: drawdown <savings> <annual%> <withdrawal%>"

    savings, annual, withdraw = map(float, nums)
    r = annual / 100
    w = withdraw / 100

    balance = savings
    years = 0
    while balance > 0 and years < 150:
        balance = balance * (1 + r) * (1 - w)
        years += 1

    if balance <= 0:
        return (
            f"With **${savings:,.0f}** and **{withdraw:.1f}%** withdrawals:\n"
            f"→ Portfolio lasts about **{years} years**."
        )

    return (
        f"With **${savings:,.0f}** and **{withdraw:.1f}%** withdrawals, "
        f"portfolio lasts **150+ years (effectively infinite)**."
    )

