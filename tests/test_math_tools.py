# tests/test_math_tools.py
from deterministic.math_tools import handle_percentage, handle_tip

def test_percentage():
    r = handle_percentage("what is 20% of 80")
    assert r is not None
    assert "16" in r.lower()

def test_tip():
    r = handle_tip("18% tip on 80")
    assert r is not None
    assert "14.40" in r.lower() or "14.4" in r.lower()

