"""Deterministic mana base analysis: for each color in the commander's
identity, compute the actual hypergeometric probability of having enough
sources by the turn it matters, and flag shortfalls against a ~90% target.

Usage:
    python3 mana_base_analysis.py --deck-dir ../review-commander-deck/decks/my-deck
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hypergeometric as hg

DECK_SIZE = 99  # library size, excluding the commander
WUBRG = set("WUBRG")

# (label, target turn to check "do we have it by now") - the target turn is
# the tier's own lower bound, i.e. "if this card wants to come down turns
# 1-2, check whether sources are reliably online by turn 2."
TIERS = [("1-2", 2), ("3-4", 4), ("5+", 5)]


def pip_counts(mana_cost: str) -> dict:
    """{color: pip count} from a mana cost string. Skips hybrid/Phyrexian
    symbols (e.g. {G/U}, {G/P}) - those are strictly easier to cast than a
    dedicated pip since either half satisfies them, and modeling that
    properly needs joint probability across combinations; skipping is a
    documented simplification, not an oversight."""
    counts = {}
    if not mana_cost:
        return counts
    front_face = mana_cost.split(" // ")[0]
    for symbol in re.findall(r"\{([^}]+)\}", front_face):
        if "/" in symbol:
            continue
        if symbol in WUBRG:
            counts[symbol] = counts.get(symbol, 0) + 1
    return counts


def curve_tier(cmc) -> str:
    if cmc is None:
        return "1-2"
    if cmc <= 2:
        return "1-2"
    if cmc <= 4:
        return "3-4"
    return "5+"


def color_sources(context: dict, color: str) -> int:
    total = 0
    for card in context["cards"]:
        if card.get("not_found"):
            continue
        if color in (card.get("produced_mana") or []):
            total += card.get("quantity", 1)
    return total


def commander_color_identity(context: dict) -> list:
    colors = set()
    for card in context["cards"]:
        if card.get("is_commander"):
            colors |= set(card.get("color_identity") or [])
    return sorted(colors)


def analyze(context: dict) -> dict:
    color_identity = commander_color_identity(context)
    sources = {c: color_sources(context, c) for c in color_identity}

    # tier -> color -> {"max_pip": int, "cards": [names with pip_count>=2]}
    tier_needs = {label: {c: {"max_pip": 0, "double_plus_pip_cards": []} for c in color_identity} for label, _ in TIERS}

    for card in context["cards"]:
        if card.get("not_found") or card.get("is_commander"):
            continue
        if "Land" in (card.get("type_line") or ""):
            continue
        pips = pip_counts(card.get("mana_cost"))
        if not pips:
            continue
        tier = curve_tier(card.get("cmc"))
        for color, count in pips.items():
            if color not in tier_needs[tier]:
                continue
            entry = tier_needs[tier][color]
            entry["max_pip"] = max(entry["max_pip"], count)
            if count >= 2:
                entry["double_plus_pip_cards"].append({"name": card["name"], "pips": count})

    results = []
    for label, target_turn in TIERS:
        cards_seen = hg.cards_seen_by_turn(target_turn, on_the_play=True)
        for color in color_identity:
            need = tier_needs[label][color]
            if need["max_pip"] == 0:
                continue
            prob = hg.probability_at_least(need["max_pip"], DECK_SIZE, sources[color], cards_seen)
            results.append({
                "tier": label,
                "target_turn": target_turn,
                "on_the_play_cards_seen": cards_seen,
                "color": color,
                "pips_needed": need["max_pip"],
                "current_sources": sources[color],
                "probability": round(prob, 3),
                "status": "OK" if prob >= hg.TARGET_PROBABILITY else "SHORTFALL",
                "at_risk_cards": need["double_plus_pip_cards"] if need["max_pip"] >= 2 else [],
            })

    return {
        "commander_color_identity": color_identity,
        "target_probability": hg.TARGET_PROBABILITY,
        "current_sources": sources,
        "tier_results": results,
        "mono_or_colorless": len(color_identity) <= 1,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    args = ap.parse_args()

    context = json.loads((args.deck_dir / "context.json").read_text())
    result = analyze(context)

    out_path = args.deck_dir / "mana_base_analysis.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")

    if result["mono_or_colorless"]:
        print("Mono-color or colorless identity - color fixing isn't a real concern here.")
    else:
        shortfalls = [r for r in result["tier_results"] if r["status"] == "SHORTFALL"]
        print(f"{len(shortfalls)} shortfall(s) found." if shortfalls else "No shortfalls at the ~90% target.")
        for s in shortfalls:
            print(f"  {s['color']} by turn {s['target_turn']} (tier {s['tier']}): "
                  f"{s['current_sources']} sources -> {s['probability']:.0%} (need {s['pips_needed']} pip(s))")


if __name__ == "__main__":
    main()
