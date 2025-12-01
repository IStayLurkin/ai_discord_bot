from godbot.deterministic.fitness_tools import (
    strength_percentile,
    generate_training_block,
    recommended_volume,
)


def test_strength_percentile_valid():
    p = strength_percentile("bench", 185, 180)
    assert p >= 0


def test_training_block():
    block = generate_training_block("ppl", "intermediate")
    assert "split" in block
    assert isinstance(block["split"], list)


def test_volume_engine():
    v = recommended_volume("chest", "advanced")
    assert "min_sets" in v
    assert v["min_sets"] > 0

