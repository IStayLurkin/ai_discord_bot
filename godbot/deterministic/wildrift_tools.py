"""
Wild Rift Deterministic Engine (Phase 6)

Pure logic, no LLM.
"""

from __future__ import annotations

from typing import Dict, List

# Phase 11.1 logging
from godbot.core.logging import get_logger

log = get_logger(__name__)


# --------------------------------------------------
# Champion Data (Minimal deterministic dataset)
# For expansion later using data/wild_rift_builds/*.md
# --------------------------------------------------

CHAMPION_ROLES = {
    "Garen": "fighter",
    "Vi": "fighter",
    "Shyvana": "fighter",
    "Darius": "fighter",
    "Kayle": "fighter",
    "Akali": "assassin",
    "Ahri": "mage",
    "Lux": "mage",
    "Morgana": "mage",
    "Annie": "mage",
    "Seraphine": "mage",
    "Zyra": "mage",
    "Miss Fortune": "marksman",
    "Jinx": "marksman",
    "Caitlyn": "marksman",
    "Lucian": "marksman",
    "Rakan": "support",
    "Nautilus": "support",
    "Leona": "support",
    "Thresh": "support",
    "Galio": "tank",
    "Malphite": "tank",
    "Volibear": "tank",
    "Warwick": "fighter",
}


# Hard CC values (VERY simplified)
CHAMPION_CC = {
    "Leona": 3,
    "Amumu": 3,
    "Nautilus": 3,
    "Thresh": 2,
    "Rakan": 2,
    "Galio": 2,
    "Malphite": 2,
    "Morgana": 1,
    "Ahri": 1,
    "Zyra": 1,
    "Lux": 1,
}


# AP/AD tags for damage distribution evaluation
CHAMPION_DAMAGE = {
    "Garen": "AD",
    "Vi": "AD",
    "Shyvana": "Mixed",
    "Darius": "AD",
    "Kayle": "Mixed",
    "Akali": "AP",
    "Ahri": "AP",
    "Lux": "AP",
    "Morgana": "AP",
    "Zyra": "AP",
    "Annie": "AP",
    "Seraphine": "AP",
    "Miss Fortune": "AD",
    "Jinx": "AD",
    "Caitlyn": "AD",
    "Lucian": "AD",
    "Galio": "AP",
    "Malphite": "AP",
    "Volibear": "Mixed",
    "Warwick": "AD",
}


# -----------------------------------------
# CC Density
# -----------------------------------------
def cc_density(team: List[str]) -> int:
    """Return the sum of CC score for a team."""
    total = 0
    for champ in team:
        total += CHAMPION_CC.get(champ, 0)
    return total


# -----------------------------------------
# AP/AD Split
# -----------------------------------------
def ap_ad_split(team: List[str]) -> Dict[str, float]:
    """Percentage composition of AP/AD/Mixed."""
    counts = {"AP": 0, "AD": 0, "Mixed": 0}

    for champ in team:
        tag = CHAMPION_DAMAGE.get(champ)
        if tag:
            counts[tag] += 1

    total = sum(counts.values())
    if total == 0:
        return counts

    return {
        "AP_pct": round((counts["AP"] / total) * 100, 1),
        "AD_pct": round((counts["AD"] / total) * 100, 1),
        "Mixed_pct": round((counts["Mixed"] / total) * 100, 1),
    }


# -----------------------------------------
# Tankiness Profile
# -----------------------------------------
TANKINESS = {
    "Galio": 8,
    "Malphite": 9,
    "Leona": 7,
    "Nautilus": 8,
    "Volibear": 7,
    "Warwick": 6,
    "Darius": 6,
    "Garen": 7,
}


def tankiness(team: List[str]) -> float:
    """Average tank score of the team."""
    if not team:
        return 0
    total = 0
    for champ in team:
        total += TANKINESS.get(champ, 3)
    return round(total / len(team), 2)


# -----------------------------------------
# Team Comp Analyzer
# -----------------------------------------
def analyze_team_comp(team: List[str]) -> Dict[str, float]:
    """Return AP/AD, CC, tank score."""
    return {
        "cc_density": cc_density(team),
        "ap_ad": ap_ad_split(team),
        "tankiness": tankiness(team),
        "team_size": len(team),
    }


# -----------------------------------------
# Counterbuild Logic
# -----------------------------------------
def counterbuild(champion: str, enemy_team: List[str]) -> List[str]:
    """
    Deterministic counter-item suggestions.
    Super simplified, expand later based on MD files.
    """
    items = []

    # heavy AP enemy
    ap_pct = ap_ad_split(enemy_team)["AP_pct"]
    if ap_pct >= 60:
        items.append("Spirit Visage")
        items.append("Wit's End")

    # heavy AD enemy
    ad_pct = ap_ad_split(enemy_team)["AD_pct"]
    if ad_pct >= 60:
        items.append("Randuin's Omen")
        items.append("Dead Man's Plate")

    # heavy CC
    if cc_density(enemy_team) >= 5:
        items.append("Mercury's Treads")

    # heavy tanks
    if tankiness(enemy_team) >= 6.5:
        items.append("Black Cleaver")

    return items


# -----------------------------------------
# Matchup Advice (deterministic note)
# -----------------------------------------
def matchup_advice(champion: str, enemy: str) -> str:
    """
    Deterministic note.
    LLM-enhanced version will be built in Phase 6.2.
    """
    champion = champion.lower()
    enemy = enemy.lower()

    if champion == "garen" and enemy in ("vayne", "kayle", "quinn"):
        return "Avoid long trades. Build early armor. Look for short Q trades."

    if champion == "vi" and enemy in ("jinx", "caitlyn", "lux"):
        return "Flank angles matter. They outrange you; engage from fog of war."

    if champion == "shyvana":
        return "Farm efficiently until level 5. Only force fights with R available."

    return "Play to your champion's win condition. Respect enemy spikes."

