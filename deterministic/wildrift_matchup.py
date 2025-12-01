# deterministic Wild Rift matchup analyzer

from dataclasses import dataclass
from typing import List, Dict


# -------------------------
# DATA TABLES
# -------------------------

AP_CHAMPS = {
    "ahri", "annie", "veigar", "lux", "morgana", "ziggs", "kayle", "akali",
    "lilia", "seraphine", "corki", "fizz", "vladimir"
}

TANK_CHAMPS = {
    "garen", "malphite", "amumu", "braum", "nautilus", "shen", "blitzcrank",
    "rammus", "sion", "leona", "mundo"
}

HIGH_CC_CHAMPS = {
    "morgana", "nautilus", "braum", "leona", "amumu", "rammus", "lulu",
    "thresh", "lux", "galio", "lissandra"
}

OBJECTIVE_MONSTERS = {
    "shyvana", "master yi", "jax", "vi", "wu kong", "nasus", "olaf",
}

HIGH_BURST = {
    "zed", "ahri", "akali", "fizz", "annie", "veigar", "rengar"
}


# -------------------------
# COMP ANALYSIS
# -------------------------

def analyze_enemy_comp(enemy_team: List[str]) -> Dict[str, float | str]:
    """
    Returns deterministic metrics about the enemy team:
    - ap_percent
    - ad_percent
    - cc_threat (low/med/high)
    - tankiness (low/med/high)
    - burst_threat (low/med/high)
    - objective_control (low/med/high)
    """

    enemy = [c.lower() for c in enemy_team]

    ap_count = sum(1 for c in enemy if c in AP_CHAMPS)
    cc_count = sum(1 for c in enemy if c in HIGH_CC_CHAMPS)
    tank_count = sum(1 for c in enemy if c in TANK_CHAMPS)
    burst_count = sum(1 for c in enemy if c in HIGH_BURST)
    obj_count = sum(1 for c in enemy if c in OBJECTIVE_MONSTERS)

    total = max(len(enemy), 1)

    ap_percent = ap_count / total
    ad_percent = 1 - ap_percent

    def level(value):
        if value >= 3:
            return "High"
        if value == 2:
            return "Medium"
        return "Low"

    return {
        "ap_damage": round(ap_percent, 2),
        "ad_damage": round(ad_percent, 2),
        "tankiness": level(tank_count),
        "cc_threat": level(cc_count),
        "burst_threat": level(burst_count),
        "objective_control": level(obj_count),
    }


# -------------------------
# CHAMPION-SPECIFIC LOGIC
# -------------------------

def counter_itemization(champion: str, analysis: dict) -> Dict[str, str]:
    """
    Hard-coded deterministic adjustments per champion based on comp analysis.
    Expandable.
    """

    champ = champion.lower()

    ap = analysis["ap_damage"]
    cc = analysis["cc_threat"]
    tanks = analysis["tankiness"]
    burst = analysis["burst_threat"]

    boots = "Plated Steelcaps" if ap < 0.4 else "Mercury's Treads"
    if cc == "High":
        boots = "Mercury's Treads"

    anti_tank = "Black Cleaver" if champ in {"garen", "vi", "shyvana"} else "Void Staff" if champ in AP_CHAMPS else None
    anti_burst = "Sterak's Gage" if champ in {"garen", "vi", "camille"} else "Hexdrinker / Maw" if burst == "High" else None

    anti_heal = (
        "Executioner's Calling" if analysis["objective_control"] == "High"
        else "Not required early"
    )

    return {
        "recommended_boots": boots,
        "anti_tank": anti_tank or "Not needed",
        "anti_burst": anti_burst or "Not needed",
        "anti_heal": anti_heal,
    }


# -------------------------
# FULL MATCHUP REPORT
# -------------------------

def full_matchup_report(your_champ: str, enemy_team: List[str]) -> str:
    analysis = analyze_enemy_comp(enemy_team)
    adjustments = counter_itemization(your_champ, analysis)

    msg = [
        "=== Enemy Composition Analysis ===",
        f"AP Damage: {analysis['ap_damage']*100:.0f}%",
        f"AD Damage: {analysis['ad_damage']*100:.0f}%",
        f"CC Threat: {analysis['cc_threat']}",
        f"Tankiness: {analysis['tankiness']}",
        f"Burst Threat: {analysis['burst_threat']}",
        f"Objective Control: {analysis['objective_control']}",
        "",
        f"=== {your_champ.title()} Adjustments ===",
        f"Boots: {adjustments['recommended_boots']}",
        f"Anti-Tank: {adjustments['anti_tank']}",
        f"Anti-Burst: {adjustments['anti_burst']}",
        f"Anti-Heal: {adjustments['anti_heal']}",
    ]

    return "\n".join(msg)

