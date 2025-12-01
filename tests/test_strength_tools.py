from deterministic.nutrition_tools import strength_level, create_training_block


def test_strength_level_bench_intermediate():
    # 100kg bench at 100kg BW -> 1.0x = intermediate by our table
    level, ratio = strength_level("bench", one_rm=100.0, bodyweight=100.0)
    assert level in {"intermediate", "advanced", "elite"}
    assert 0.95 <= ratio <= 1.05


def test_strength_level_squat_advanced():
    # 180kg squat at 90kg BW -> 2.0x BW ~ advanced
    level, ratio = strength_level("squat", one_rm=180.0, bodyweight=90.0)
    assert ratio == 2.0
    assert level in {"advanced", "elite"}


def test_training_block_ppl_has_days():
    block = create_training_block("PPL")
    assert "Push" in block
    assert "Pull" in block
    assert "Legs" in block
    assert isinstance(block["Push"], list)
    assert len(block["Push"]) > 0


def test_training_block_unknown_style():
    block = create_training_block("XYZ")
    assert "error" in block

