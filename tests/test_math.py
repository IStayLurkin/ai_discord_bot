"""
Basic math tools sanity test.
Tests that deterministic math operations work correctly.
"""

import math


def test_math_basic():
    """Basic math sanity checks."""
    assert 2 + 3 == 5
    assert 4 * 2 == 8
    assert math.sqrt(16) == 4.0


def test_math_precision():
    """Test floating point precision."""
    assert abs(0.1 + 0.2 - 0.3) < 1e-10

