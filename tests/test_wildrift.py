from godbot.deterministic.wildrift_tools import (
    cc_density,
    ap_ad_split,
    analyze_team_comp,
    counterbuild,
)


def test_cc_density():
    assert cc_density(["Leona", "Lux"]) >= 1


def test_ap_ad_split():
    split = ap_ad_split(["Ahri", "Garen"])
    assert split["AP_pct"] >= 0
    assert split["AD_pct"] >= 0


def test_team_comp():
    res = analyze_team_comp(["Ahri", "Garen", "Vi"])
    assert "cc_density" in res
    assert "tankiness" in res


def test_counterbuild():
    items = counterbuild("Garen", ["Ahri", "Lux", "Zyra"])
    assert isinstance(items, list)

