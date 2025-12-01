from deterministic.wildrift_matchup import (
    analyze_enemy_comp,
    full_matchup_report,
)


def test_analyze_enemy_comp_ap_heavy():
    enemy_team = ["Ahri", "Annie", "Veigar", "Garen", "Vi"]
    analysis = analyze_enemy_comp(enemy_team)

    # 3/5 AP
    assert analysis["ap_damage"] > 0.5
    assert analysis["ad_damage"] < 0.5

    # There's at least some CC and burst in that comp
    assert analysis["cc_threat"] in {"Medium", "High"}
    assert analysis["burst_threat"] in {"Medium", "High"}


def test_full_matchup_report_contains_sections():
    your_champ = "Garen"
    enemy_team = ["Morgana", "Veigar", "Vi", "Draven", "Gnar"]
    report = full_matchup_report(your_champ, enemy_team)

    assert "Enemy Composition Analysis" in report
    assert "Garen Adjustments" in report
    assert "Boots:" in report
    assert "Anti-Tank:" in report
    assert "Anti-Burst:" in report

