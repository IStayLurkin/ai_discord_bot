# tests/test_matchup_detection.py
from deterministic.wildrift_tools import detect_matchup, CHAMPION_BUILDS

def test_basic_matchup():
    """Test basic matchup detection"""
    if "garen" in CHAMPION_BUILDS and "fiora" in CHAMPION_BUILDS:
        m = detect_matchup("garen vs fiora")
        assert m is not None
        assert m["primary"] == "garen"
        assert "fiora" in m["opponents"]

def test_matchup_with_counter():
    """Test matchup detection with 'counter' keyword"""
    if "garen" in CHAMPION_BUILDS and "darius" in CHAMPION_BUILDS:
        m = detect_matchup("counter darius as garen")
        assert m is not None
        assert m["primary"] == "garen"
        assert "darius" in m["opponents"]

