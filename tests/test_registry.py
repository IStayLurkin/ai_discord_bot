# tests/test_registry.py
from deterministic.registry import try_deterministic_tools

def test_registry_loaded():
    """Test that the registry system is functional"""
    # Test with a simple math query
    result = try_deterministic_tools("what is 2+2")
    assert result is not None
    assert "4" in result

