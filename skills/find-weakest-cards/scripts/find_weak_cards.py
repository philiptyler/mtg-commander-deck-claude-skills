"""Surface candidate-for-cutting signals from an already-reviewed deck.

This does NOT rank or pick "the weakest N cards" itself - it computes
objective, checkable signals (category oversaturation, cards with no
detected functional role, high-CMC single-purpose cards, land quality
issues) and leaves the actual judgment call to whoever reads the output
(you, or Claude synthesizing an answer to a specific question like
"what are the weakest 2 removal spells").

Requires review-commander-deck's context.json and analysis.json to already
exist for this deck - run that skill's pipeline first if they don't.

Usage:
    python3 find_weak_cards.py --deck-dir ../review-commander-deck/decks/my-deck
"""

import argparse
import json
import re
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent.parent

# See ../references/category_targets.md for sourcing/rationale. Keyed by
# bracket number, each category maps to an inclusive (min, max) range.
TARGET_RANGES = {
    1: {"lands": (36, 40), "ramp": (6, 12), "card_draw": (6, 12), "targeted_removal": (4, 12), "board_wipe": (0, 3), "tutors": (0, 3)},
    2: {"lands": (36, 38), "ramp": (8, 10), "card_draw": (8, 10), "targeted_removal": (8, 10), "board_wipe": (1, 3), "tutors": (0, 3)},
    3: {"lands": (35, 38), "ramp": (10, 12), "card_draw": (10, 12), "targeted_removal": (10, 14), "board_wipe": (2, 3), "tutors": (3, 6)},
    4: {"lands": (33, 36), "ramp": (10, 13), "card_draw": (10, 14), "targeted_removal": (12, 16), "board_wipe": (2, 4), "tutors": (5, 9)},
    5: {"lands": (30, 34), "ramp": (13, 16), "card_draw": (8, 12), "targeted_removal": (10, 15), "board_wipe": (1, 3), "tutors": (8, 14)},
}

ALL_CATEGORY_KEYS = [
    "ramp", "targeted_removal", "board_wipe", "counterspell", "card_draw",
    "land_tutor", "nonland_tutor", "extra_turn", "mass_land_denial", "game_changer",
]

# Heuristic only - a land can have real upside phrased in ways this misses.
# "if you don't" catches the current shockland templating ("you may pay 2
# life. If you don't, it enters tapped."), which replaced the old "unless
# you pay 2 life" wording and would otherwise be missed entirely.
TAPPED_UPSIDE_HINTS = ["unless", "if you don't", "scry", "surveil", "gain 1 life", "gain life", "draw a card", "you may reveal"]


def parse_bracket(analysis: dict) -> int:
    suggested = analysis.get("bracket_estimate", {}).get("suggested", "")
    m = re.search(r"\d", suggested)
    return int(m.group()) if m else 3


def category_saturation(analysis: dict, bracket: int) -> list:
    categories = analysis["categories"]
    counts = analysis["counts"]
    actual = {
        "lands": counts.get("lands", 0),
        "ramp": len(categories.get("ramp", [])),
        "card_draw": len(categories.get("card_draw", [])),
        "targeted_removal": len(categories.get("targeted_removal", [])),
        "board_wipe": len(categories.get("board_wipe", [])),
        # Nonland tutors only - fetchlands are a mana-base/consistency tool,
        # not the same "silver bullet density" signal a Vampiric Tutor is.
        "tutors": len(categories.get("nonland_tutor", [])),
    }
    targets = TARGET_RANGES[bracket]
    results = []
    for category, count in actual.items():
        lo, hi = targets[category]
        status = "under" if count < lo else "over" if count > hi else "within"
        results.append({"category": category, "count": count, "target_range": [lo, hi], "status": status})
    return results


def build_category_index(analysis: dict) -> dict:
    index = {}
    for key in ALL_CATEGORY_KEYS:
        for name in analysis["categories"].get(key, []):
            index.setdefault(name, set()).add(key)
    return index


def roleless_nonland_cards(context: dict, category_index: dict) -> list:
    out = []
    for card in context["cards"]:
        if card.get("not_found") or card.get("is_commander"):
            continue
        if "Land" in (card.get("type_line") or ""):
            continue
        if card["name"] not in category_index:
            out.append({"name": card["name"], "cmc": card.get("cmc"), "type_line": card.get("type_line")})
    return out


def high_cmc_low_role_cards(context: dict, category_index: dict, cmc_floor: int = 6) -> list:
    out = []
    for card in context["cards"]:
        if card.get("not_found") or card.get("is_commander"):
            continue
        if "Land" in (card.get("type_line") or ""):
            continue
        cmc = card.get("cmc")
        if cmc is None or cmc < cmc_floor:
            continue
        roles = sorted(category_index.get(card["name"], set()))
        if len(roles) <= 1:
            out.append({"name": card["name"], "cmc": cmc, "roles": roles})
    return out


def land_signals(context: dict, deck_colors: set) -> list:
    out = []
    for card in context["cards"]:
        if card.get("not_found"):
            continue
        type_line = card.get("type_line") or ""
        if "Land" not in type_line:
            continue
        oracle = (card.get("oracle_text") or "").lower()
        enters_tapped = bool(re.search(r"enters (the battlefield )?tapped", oracle))
        has_upside_hint = any(hint in oracle for hint in TAPPED_UPSIDE_HINTS)
        produced = set(card.get("produced_mana") or [])
        colored_produced = produced - {"C"}
        # Flag only when it produces a color and none of those colors are
        # in the deck's identity - a colorless-only utility land (Command
        # Tower analog, Wastes, etc.) isn't "off color," it's a different
        # question entirely.
        off_color = bool(deck_colors) and bool(colored_produced) and colored_produced.isdisjoint(deck_colors)
        out.append({
            "name": card["name"],
            "is_basic": "Basic" in type_line,
            "enters_tapped": enters_tapped,
            "enters_tapped_no_upside_hint": enters_tapped and not has_upside_hint,
            "produced_mana": sorted(produced),
            "off_color": off_color,
        })
    return out


def analyze(context: dict, analysis: dict) -> dict:
    bracket = parse_bracket(analysis)
    category_index = build_category_index(analysis)
    deck_colors = set(analysis.get("color_identity_pip_counts", {}).keys())

    return {
        "bracket_used_for_targets": bracket,
        "category_saturation": category_saturation(analysis, bracket),
        "roleless_nonland_cards": roleless_nonland_cards(context, category_index),
        "high_cmc_low_role_cards": high_cmc_low_role_cards(context, category_index),
        "land_signals": land_signals(context, deck_colors),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path,
                     help="Path to a deck folder already built by review-commander-deck "
                          "(must contain context.json and analysis.json)")
    args = ap.parse_args()

    context = json.loads((args.deck_dir / "context.json").read_text())
    analysis = json.loads((args.deck_dir / "analysis.json").read_text())

    result = analyze(context, analysis)
    out_path = args.deck_dir / "weak_card_signals.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
    print(f"Bracket used for targets: {result['bracket_used_for_targets']}")


if __name__ == "__main__":
    main()
