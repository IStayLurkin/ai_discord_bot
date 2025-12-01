# tests/test_fitness_tools.py
from deterministic.fitness_tools import handle_1rm, epley_1rm, reverse_epley

def test_1rm_bench():
    r = handle_1rm("bench 200 for 5 reps what is my 1rm")
    assert r is not None
    assert "233" in r or "233.3" in r

def test_epley_formula():
    result = epley_1rm(200, 5)
    assert abs(result - 233.33) < 1.0

def test_reverse_epley():
    result = reverse_epley(300, 8)
    assert result > 200 and result < 250

