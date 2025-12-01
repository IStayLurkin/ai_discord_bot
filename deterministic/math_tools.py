# deterministic/math_tools.py
import re
import ast
import operator as op
from typing import Optional
from .registry import register_handler

# ---------- safe math eval ----------

_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

def _eval_ast(node):
    if isinstance(node, ast.Num):  # Py <=3.7
        return node.n
    if isinstance(node, ast.Constant):  # Py 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only int/float constants allowed")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("Unsupported expression")

def eval_math_expression(expr: str) -> float:
    parsed = ast.parse(expr, mode="eval")
    return _eval_ast(parsed.body)

@register_handler(priority=50)
def handle_simple_math(text: str) -> Optional[str]:
    lower = text.lower()
    trigger_words = ["what is", "what's", "calculate", "how much is", "solve", "="]
    has_trigger = any(w in lower for w in trigger_words)
    has_digit = any(ch.isdigit() for ch in text)
    has_op = any(ch in "+-*/^" for ch in text)

    if not (has_trigger and has_digit and has_op):
        return None

    match = re.search(r"([-+*/^().\d\s]+)", text)
    if not match:
        return None

    expr = match.group(1).strip().replace("^", "**")
    try:
        result = eval_math_expression(expr)
    except Exception:
        return None

    return f"{expr} = **{result}**"

# ---------- unit conversions ----------

@register_handler(priority=60)
def handle_unit_conversion(text: str) -> Optional[str]:
    lower = text.lower().strip()

    # lbs <-> kg
    m = re.search(r"(\d+(\.\d+)?)\s*(lbs|lb|pounds)\s*(to|in)\s*(kg|kilograms)", lower)
    if m:
        val = float(m.group(1))
        kg = val * 0.45359237
        return f"**{val:.2f} lbs** ≈ **{kg:.2f} kg**"

    m = re.search(r"(\d+(\.\d+)?)\s*(kg|kilograms)\s*(to|in)\s*(lbs|lb|pounds)", lower)
    if m:
        val = float(m.group(1))
        lbs = val / 0.45359237
        return f"**{val:.2f} kg** ≈ **{lbs:.2f} lbs**"

    # cm <-> inches
    m = re.search(r"(\d+(\.\d+)?)\s*(cm|centimeters)\s*(to|in)\s*(inches|inch|in)", lower)
    if m:
        val = float(m.group(1))
        inches = val / 2.54
        return f"**{val:.2f} cm** ≈ **{inches:.2f} in**"

    m = re.search(r"(\d+(\.\d+)?)\s*(inches|inch|in)\s*(to|in)\s*(cm|centimeters)", lower)
    if m:
        val = float(m.group(1))
        cm = val * 2.54
        return f"**{val:.2f} in** ≈ **{cm:.2f} cm**"

    # C <-> F
    m = re.search(r"(\d+(\.\d+)?)\s*c\s*(to|in)\s*f", lower)
    if m:
        c = float(m.group(1))
        f = c * 9.0/5.0 + 32
        return f"**{c:.2f}°C** ≈ **{f:.2f}°F**"

    m = re.search(r"(\d+(\.\d+)?)\s*f\s*(to|in)\s*c", lower)
    if m:
        f = float(m.group(1))
        c = (f - 32) * 5.0/9.0
        return f"**{f:.2f}°F** ≈ **{c:.2f}°C**"

    return None

# ---------- percentages / tips ----------

@register_handler(priority=65)
def handle_percentage(text: str) -> Optional[str]:
    lower = text.lower()

    m = re.search(r"(\d+(\.\d+)?)\s*%\s*of\s*(\d+(\.\d+)?)", lower)
    if m:
        pct = float(m.group(1))
        base = float(m.group(3))
        val = base * pct / 100.0
        return f"**{pct:.2f}%** of **{base:.2f}** is **{val:.2f}**"

    m = re.search(r"(increase|decrease)\s+(\d+(\.\d+)?)\s+by\s+(\d+(\.\d+)?)\s*%", lower)
    if m:
        direction = m.group(1)
        base = float(m.group(2))
        pct = float(m.group(4))
        delta = base * pct / 100.0
        new_val = base + delta if direction == "increase" else base - delta
        return (
            f"{direction.title()} **{base:.2f}** by **{pct:.2f}%** → **{new_val:.2f}** "
            f"(change of {delta:.2f})."
        )

    return None

@register_handler(priority=70)
def handle_tip(text: str) -> Optional[str]:
    lower = text.lower()
    if "tip" not in lower and "gratuity" not in lower:
        return None

    m = re.search(r"(\d+(\.\d+)?)\s*%\s*(tip|gratuity)\s*(on)?\s*(\d+(\.\d+)?)", lower)
    if m:
        pct = float(m.group(1))
        bill = float(m.group(5))
        tip_val = bill * pct / 100.0
        total = bill + tip_val
        return (
            f"**{pct:.1f}%** tip on **{bill:.2f}** is **{tip_val:.2f}**.\n"
            f"Total bill with tip: **{total:.2f}**"
        )
    return None

