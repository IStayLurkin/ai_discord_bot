# deterministic/wildrift_tools.py
import os
import re
import json
from typing import Optional, Dict, Any
from difflib import get_close_matches
from .registry import register_handler

BUILD_DIR = os.path.join(os.getcwd(), "data", "wild_rift_builds")

# Cache loads once at startup
CHAMPION_BUILDS = {}


def load_builds():
    """Load all champion build files from /data/wild_rift_builds/*.md"""
    if not os.path.exists(BUILD_DIR):
        return

    for file in os.listdir(BUILD_DIR):
        if file.lower().endswith(".md"):
            champ = file.replace(".md", "").lower()
            try:
                path = os.path.join(BUILD_DIR, file)
                with open(path, "r", encoding="utf-8") as f:
                    CHAMPION_BUILDS[champ] = f.read()
            except Exception as e:
                print(f"[WildRift] Failed to load {file}: {e}")


# Load at import
load_builds()


def find_champ(name: str) -> Optional[str]:
    """Fuzzy match champion name to loaded builds"""
    name = name.lower().strip()

    if name in CHAMPION_BUILDS:
        return name

    matches = get_close_matches(name, CHAMPION_BUILDS.keys(), n=1, cutoff=0.5)
    return matches[0] if matches else None


# ==========================================================
# PHASE 6 — WILD RIFT BUILDER V2
# ==========================================================

@register_handler(priority=90)
def handle_wildrift_build(text: str) -> Optional[str]:
    """
    wild rift <champ> build
    or:
    <champ> build
    or:
    build <champ>
    """
    lower = text.lower()

    # Detect trigger
    if "build" not in lower and "wild rift" not in lower:
        return None

    # Extract champ name (very flexible)
    # Examples:
    # "wild rift garen build"
    # "give me the best vi build"
    # "garen build"
    # "build jinx"
    tokens = re.split(r"\s+", lower)
    possible_names = [t for t in tokens if t not in ["wild", "rift", "build", "best", "a", "the", "show", "me"]]

    if not possible_names:
        # If no champ found but build/wild rift mentioned, show available champs
        if CHAMPION_BUILDS:
            champ_list = ", ".join(sorted([c.capitalize() for c in CHAMPION_BUILDS.keys()]))
            return (
                "I have builds for these champs:\n"
                f"`{champ_list}`\n"
                "Ask like: `wild rift garen build` or `vi build`."
            )
        return None

    guess = find_champ(possible_names[-1])
    if not guess:
        # Show available champs if fuzzy match fails
        if CHAMPION_BUILDS:
            champ_list = ", ".join(sorted([c.capitalize() for c in CHAMPION_BUILDS.keys()]))
            return (
                f"Couldn't find a build for that champion.\n"
                f"Available champs: `{champ_list}`"
            )
        return None

    build_text = CHAMPION_BUILDS.get(guess)
    if not build_text:
        return f"No build data found for **{guess.capitalize()}**."

    return (
        f"**Wild Rift Build — {guess.capitalize()}**\n\n"
        f"{build_text}"
    )


# ==========================================================
# PHASE 7 — MATCHUP ANALYZER V1
# ==========================================================

ROLES_PATH = os.path.join(os.getcwd(), "data", "champion_roles.json")

# Load champion roles
try:
    with open(ROLES_PATH, "r", encoding="utf-8") as f:
        CHAMPION_ROLES = json.load(f)
except:
    CHAMPION_ROLES = {}


def detect_matchup(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts champions from X vs Y type messages.
    Supports:
        garen vs fiora
        vi vs jinx morg braum
        counter yasuo as garen
        struggling vs darius
    """
    lower = text.lower()

    if " vs " not in lower and "counter" not in lower and "beat" not in lower and "into" not in lower and "struggling" not in lower:
        return None

    # All known champs from build DB
    champ_list = list(CHAMPION_BUILDS.keys())

    found = []
    for word in re.split(r"[^a-zA-Z]", lower):
        name = word.strip()
        if not name:
            continue
        match = find_champ(name)
        if match and match not in found:
            found.append(match)

    if len(found) < 2:
        return None

    # Attacker = first champion found
    # Defender(s) = rest
    return {
        "primary": found[0],
        "opponents": found[1:]
    }


def get_role(champ: str) -> str:
    champ = champ.lower()
    for role, clist in CHAMPION_ROLES.items():
        if champ in clist:
            return role
    return "unknown"


@register_handler(priority=91)
def handle_wildrift_matchup(text: str) -> Optional[Dict[str, Any]]:
    """Detect champion matchups and prepare context for the LLM."""

    matchup = detect_matchup(text)
    if not matchup:
        return None

    primary = matchup["primary"]
    opponents = matchup["opponents"]

    primary_role = get_role(primary)

    opp_data = []
    for opp in opponents:
        role = get_role(opp)
        opp_data.append(f"{opp.capitalize()} ({role})")

    # Include build context if available
    primary_build = CHAMPION_BUILDS.get(primary, "(no build data)")
    enemy_builds = {opp: CHAMPION_BUILDS.get(opp, "(no build data)") for opp in opponents}

    # Prepare context for LLM
    context = (
        "WILD RIFT MATCHUP ANALYSIS REQUEST\n\n"
        f"Primary Champion: {primary.capitalize()} ({primary_role})\n"
        f"Opponents: {', '.join(opp_data)}\n\n"
        "=== PRIMARY BUILD ===\n"
        f"{primary_build}\n\n"
        "=== OPPONENT BUILDS ===\n"
    )

    for opp in opponents:
        context += f"\n{opp.capitalize()}:\n{enemy_builds[opp]}\n"

    context += (
        "\nGUIDELINES FOR ANALYSIS:\n"
        "- Provide laning strategy\n"
        "- Provide trading pattern\n"
        "- Identify enemy power spikes\n"
        "- Recommend itemization adjustments\n"
        "- Recommend best boots\n"
        "- Recommend runes if different\n"
        "- Give 3–5 practical tips\n"
        "- Avoid hallucinating nonexistent skills or items\n"
        "- Refer ONLY to the builds provided above\n"
    )

    return {
        "matchup_context": context,
        "primary_champion": primary.capitalize(),
        "opponents": [x.capitalize() for x in opponents]
    }
