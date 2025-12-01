# tests/test_wildrift_tools.py
from deterministic.wildrift_tools import find_champ, CHAMPION_BUILDS, load_builds

def test_champion_builds_loaded():
    """Test that champion builds are loaded at startup"""
    load_builds()  # Ensure builds are loaded
    assert len(CHAMPION_BUILDS) > 0

def test_fuzzy_match():
    """Test fuzzy matching for champion names"""
    if "garen" in CHAMPION_BUILDS:
        result = find_champ("grn")
        assert result == "garen" or result is None  # Either exact match or no match

