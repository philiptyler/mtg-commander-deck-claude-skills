"""Compute deck statistics from context.json: curve, ramp, removal, draw,
tutors, extra turns, mass land denial, Game Changers, and a suggested
Commander Bracket (1-5).

This is heuristic, regex-based analysis over oracle text. It will
misclassify some cards (e.g. novel phrasing, split/adventure cards) — treat
counts as a strong starting point for the review, not ground truth. See
references/bracket_rubric.md for what each category means and why.

Usage:
    python3 analyze_deck.py --deck-dir decks/my-deck
"""

import argparse
import json
import re
from pathlib import Path

# --- category heuristics -----------------------------------------------
# Each is a list of regexes checked against lowercased oracle_text. A card
# can match more than one category (e.g. a ramp spell that also draws).

RAMP_PATTERNS = [
    r"search your library for a basic land card",
    r"search your library for a land card",
    r"search your library for an? (forest|island|swamp|mountain|plains) card",
    r"add \{[cwubrg]\}",
    r"add (?:an additional )?(one|two|three) mana (of any (one )?color|in any combination of colors)",
    r"add \{[cwubrg]\}\{[cwubrg]\}",
    r"lands? you control.*(?:untap|additional)",
    r"you may play an additional land",
    # Classic mana-doubler templating (Mirari's Wake, Zendikar Resurgent, ...)
    # - catches it regardless of exactly how the extra mana is worded ("of
    # any type that land produced", "of any color", etc.), since the
    # distinctive, low-false-positive-risk part is "tap a land for mana,
    # add" itself. Found because Mirari's Wake, added to the dinos deck,
    # wasn't recognized as ramp at all - the existing pattern only expected
    # "of any color," not "of any type."
    r"whenever you tap a land for mana, add",
]

_UP_TO = r"(?:up to \w+ )?"
_QUALIFIER = r"(?:[\w-]+ )?"  # e.g. "nonland", "non-Dinosaur", "red" before the noun
# destroy/exile-target removal needs a per-sentence check, not a plain regex:
# "exile up to one target artifact or creature you control" has "you control"
# apply to both nouns, past where a lookahead right after the first noun
# would see it — so this is checked separately in _has_opponent_removal().
_DESTROY_EXILE_TARGET_RE = re.compile(
    rf"(?:destroy|exile) {_UP_TO}target {_QUALIFIER}(creature|permanent|artifact|enchantment|planeswalker)"
)

_TARGET_VICTIM = r"(?:another )?target (creature|player|planeswalker)|any target"
TARGETED_REMOVAL_PATTERNS = [
    rf"deals? \d+ damage to ({_TARGET_VICTIM})",
    rf"deals? damage equal to .{{0,40}}? to ({_TARGET_VICTIM})",
    rf"that much damage to ({_TARGET_VICTIM})",
    r"target creature gets -\d+/-\d+",
    r"return target (creature|permanent|nonland permanent) to its owner's hand",
    r"gain control of target creature",
]


# "you own" is the same exclusion as "you control" - Magic uses it on
# effects like Sword of Hearth and Home ("exile up to one target creature
# you own") specifically because ownership persists even through a theft
# effect, where "you control" wouldn't. Found because that exact card got
# miscategorized as removal for blinking your own creature - the "you
# control" exclusion this check already had didn't cover the synonym.
_OWN_PERMANENT_MARKERS = ("you control", "you own")


def _has_opponent_removal(text: str) -> bool:
    for sentence in re.split(r"(?<=[.;])\s+", text):
        if _DESTROY_EXILE_TARGET_RE.search(sentence) and not any(m in sentence for m in _OWN_PERMANENT_MARKERS):
            return True
    return False

BOARD_WIPE_PATTERNS = [
    rf"destroy all {_QUALIFIER}(creatures|permanents)",
    rf"exile all {_QUALIFIER}(creatures|permanents)",
    r"each (creature|player)'s? .*(-\d+/-\d+|sacrifices?)",
    r"all creatures get -\d+/-\d+",
]
# Handled separately (needs a magnitude check, not just presence):
BOARD_WIPE_DAMAGE_RE = re.compile(r"deals? (\d+) damage to each creature")
BOARD_WIPE_DAMAGE_MIN = 2  # below this it's incidental chip damage, not a sweeper

COUNTERSPELL_PATTERNS = [
    r"counter target spell",
]

_NUMBER_WORDS = r"a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+|that many|x"
CARD_DRAW_PATTERNS = [
    rf"draws? ({_NUMBER_WORDS}) cards?",
    rf"draws? ({_NUMBER_WORDS}) additional cards?",
    r"draws? a card for each",
    r"draws? cards? equal to",
]

EXTRA_TURN_PATTERNS = [
    r"take an extra turn",
    r"extra turns? after this one",
]

MASS_LAND_DENIAL_PATTERNS = [
    r"destroy all lands",
    r"each player sacrifices a land",
    r"target player sacrifices a land",
    r"lands? don't untap",
    r"players can't (search their libraries|play lands)",
]

# Not mana ramp (doesn't increase available mana), but a real functional
# role that was previously invisible to this script: getting a creature
# onto the battlefield for less than its full cost, which in an ETB-trigger
# -heavy deck (this repo's example deck included) means more triggers per
# turn than raw mana would otherwise allow. Added after direct user
# feedback: Hunting Velociraptor (prowl) and Tannuk, Steadfast Second
# (warp) were both dismissed as "roleless" by this script and undervalued
# in a review as a result, when their actual job - cheaper access to a big
# Dinosaur, meaning another ETB trigger sooner - was real and worth seeing.
COST_REDUCTION_PATTERNS = [
    r"have prowl",
    r"have warp",
    r"spells you cast cost \{\d+\} less",
    r"creature spells you cast cost \{\d+\} less",
    r"costs? \{\d+\} less to cast",
]

TYPE_CATEGORIES = ["Creature", "Instant", "Sorcery", "Artifact", "Enchantment", "Planeswalker", "Battle", "Land"]
TYPE_COUNT_KEYS = {
    "Creature": "creatures", "Instant": "instants", "Sorcery": "sorceries",
    "Artifact": "artifacts", "Enchantment": "enchantments",
    "Planeswalker": "planeswalkers", "Battle": "battles",
}


def _matches_any(text: str, patterns) -> bool:
    return any(re.search(p, text) for p in patterns)


def _is_land_tutor_sentence(sentence: str) -> bool:
    return "land" in sentence


def classify_card(card: dict) -> dict:
    text = (card.get("oracle_text") or "").lower()
    type_line = card.get("type_line") or ""
    is_land = "Land" in type_line
    tags = set()

    if is_land:
        tags.add("land")

    # A land's own "tap for mana" ability isn't ramp (that's just its mana
    # base doing its job) - only count ramp from nonland sources (rocks,
    # dorks, rituals, land-fetch spells).
    if not is_land and _matches_any(text, RAMP_PATTERNS):
        tags.add("ramp")
    if _has_opponent_removal(text) or _matches_any(text, TARGETED_REMOVAL_PATTERNS):
        tags.add("targeted_removal")
    damage_match = BOARD_WIPE_DAMAGE_RE.search(text)
    is_damage_wipe = damage_match and int(damage_match.group(1)) >= BOARD_WIPE_DAMAGE_MIN
    if _matches_any(text, BOARD_WIPE_PATTERNS) or is_damage_wipe:
        tags.add("board_wipe")
    if _matches_any(text, COUNTERSPELL_PATTERNS):
        tags.add("counterspell")
    if _matches_any(text, CARD_DRAW_PATTERNS):
        tags.add("card_draw")
    if _matches_any(text, EXTRA_TURN_PATTERNS):
        tags.add("extra_turn")
    if _matches_any(text, MASS_LAND_DENIAL_PATTERNS):
        tags.add("mass_land_denial")
    if _matches_any(text, COST_REDUCTION_PATTERNS):
        tags.add("cost_reduction")

    for sentence in re.split(r"(?<=[.;])\s+", text):
        if "search your library for" in sentence:
            if _is_land_tutor_sentence(sentence):
                tags.add("land_tutor")
            else:
                tags.add("nonland_tutor")

    if card.get("game_changer"):
        tags.add("game_changer")

    return tags


def curve_bucket(cmc) -> str:
    if cmc is None:
        return "unknown"
    cmc = int(cmc)
    return str(cmc) if cmc < 7 else "7+"


def analyze(context: dict) -> dict:
    cards = context["cards"]

    counts = {"total_cards": context["card_count"], "lands": 0}
    for key in TYPE_COUNT_KEYS.values():
        counts[key] = 0

    curve = {}
    color_identity_counts = {}
    categories = {
        "ramp": [], "targeted_removal": [], "board_wipe": [], "counterspell": [],
        "card_draw": [], "land_tutor": [], "nonland_tutor": [],
        "extra_turn": [], "mass_land_denial": [], "game_changer": [],
        "cost_reduction": [],
    }

    for card in cards:
        if card.get("not_found"):
            continue
        qty = card.get("quantity", 1)
        type_line = card.get("type_line") or ""

        if "Land" in type_line:
            counts["lands"] += qty
        else:
            for t, key in TYPE_COUNT_KEYS.items():
                if t in type_line:
                    counts[key] += qty
            bucket = curve_bucket(card.get("cmc"))
            curve[bucket] = curve.get(bucket, 0) + qty

        for color in card.get("color_identity") or []:
            color_identity_counts[color] = color_identity_counts.get(color, 0) + qty

        for tag in classify_card(card):
            if tag in categories:
                categories[tag].append(card["name"])
            elif tag == "land":
                pass

    game_changer_count = len(categories["game_changer"])
    has_mld = len(categories["mass_land_denial"]) > 0
    extra_turn_count = len(categories["extra_turn"])

    bracket = estimate_bracket(game_changer_count, has_mld, extra_turn_count)

    return {
        "counts": counts,
        "mana_curve": dict(sorted(curve.items(), key=lambda kv: (kv[0] == "unknown", kv[0]))),
        "color_identity_pip_counts": color_identity_counts,
        "categories": categories,
        "bracket_estimate": bracket,
    }


def estimate_bracket(game_changer_count: int, has_mld: bool, extra_turn_count: int) -> dict:
    """Heuristic bracket suggestion per references/bracket_rubric.md.

    This only encodes the mechanically-checkable parts of WotC's criteria
    (Game Changer count, mass land denial, extra-turn density). It can't
    see two-card infinite combos or judge "casual intent" — those need a
    human (or Claude reading the actual decklist) to weigh in, so they're
    surfaced as caveats rather than folded into the number.
    """
    caveats = [
        "Two-card infinite combo potential can't be detected from card text "
        "alone — review the tutor/combo-piece cards in categories.nonland_tutor "
        "and categories.game_changer by hand.",
        "Bracket 1 vs. 2 and Bracket 4 vs. 5 hinge on player/table intent "
        "(casual theme vs. optimized, tournament meta vs. not), not just card "
        "choices — this script can't infer that.",
    ]

    if has_mld:
        suggested = "4 (Optimized) or higher"
        reason = (
            "Contains mass land denial, which Brackets 1-3 explicitly disallow."
        )
    elif game_changer_count > 3:
        suggested = "4 (Optimized) or higher"
        reason = (
            f"Contains {game_changer_count} Game Changers; Bracket 3 caps at 3."
        )
    elif 1 <= game_changer_count <= 3:
        suggested = "3 (Upgraded)"
        reason = f"Contains {game_changer_count} Game Changer(s), within Bracket 3's limit of 3."
    else:
        suggested = "2 (Core) or 1 (Exhibition)"
        reason = "No Game Changers or mass land denial detected."

    if extra_turn_count > 2 and "3" in suggested:
        caveats.append(
            f"{extra_turn_count} extra-turn cards detected — Bracket 3 expects these "
            "'only in low quantities, not chained/looped'; worth a manual look."
        )

    return {"suggested": suggested, "reasoning": reason, "caveats": caveats}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    args = ap.parse_args()

    context = json.loads((args.deck_dir / "context.json").read_text())
    analysis = analyze(context)

    out_path = args.deck_dir / "analysis.json"
    out_path.write_text(json.dumps(analysis, indent=2))
    print(f"Wrote {out_path}")
    print(f"Bracket estimate: {analysis['bracket_estimate']['suggested']}")


if __name__ == "__main__":
    main()
