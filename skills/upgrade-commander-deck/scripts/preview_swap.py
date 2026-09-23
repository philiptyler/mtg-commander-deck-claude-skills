"""Preview the curve/category impact of a proposed swap WITHOUT touching
the decklist. Direct feedback: curve was only ever being computed AFTER a
swap was applied (update-commander-deck's diff), meaning a proposal was
either backed by no real numbers or by numbers nobody had actually
computed yet. This lets curve (and category) impact be part of the
proposal itself, before anyone confirms anything.

Builds a modified in-memory copy of context.json (cut card removed, add
card's real Scryfall data inserted), writes it to a scratch directory, and
runs review-commander-deck's actual analyze_deck.py against it via
subprocess - reusing the real computation rather than a second copy of the
effective-CMC/curve logic that could drift out of sync with it. This
mirrors how skills in this repo already call each other's scripts (e.g.
review-commander-deck calling find-deck-combos); it does not import
analyze_deck.py directly, to keep this skill independently installable.

Usage:
    python3 preview_swap.py --deck-dir ../review-commander-deck/decks/my-deck \
        --cut "Card Being Cut" --add "Card Being Added"
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scryfall_search_client
from find_upgrade_candidates import normalize_card

ANALYZE_SCRIPT = Path(__file__).resolve().parent.parent.parent / "review-commander-deck" / "scripts" / "analyze_deck.py"

CARD_FIELDS = [
    "name", "mana_cost", "cmc", "type_line", "oracle_text",
    "color_identity", "colors", "game_changer",
    "power", "toughness", "loyalty", "keywords", "produced_mana",
]


def card_summary(card: dict) -> dict:
    summary = {field: card.get(field) for field in CARD_FIELDS}
    summary["commander_legal"] = card.get("legalities", {}).get("commander")
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    ap.add_argument("--cut", required=True, help="exact name of the card being removed")
    ap.add_argument("--add", required=True, help="exact name of the card being added")
    args = ap.parse_args()

    if not ANALYZE_SCRIPT.exists():
        print("review-commander-deck not found alongside this skill - can't preview.")
        return

    context = json.loads((args.deck_dir / "context.json").read_text())
    before_analysis = json.loads((args.deck_dir / "analysis.json").read_text())

    cards = [c for c in context["cards"] if c["name"] != args.cut]
    if len(cards) == len(context["cards"]):
        print(f"WARNING: '{args.cut}' wasn't found in this deck's context.json - check the exact name.")

    lookup = scryfall_search_client.lookup_by_names([args.add])
    raw_add_card = lookup.get(args.add)
    if raw_add_card is None:
        print(f"Couldn't resolve '{args.add}' on Scryfall - check the exact name.")
        return
    raw_add_card = normalize_card(raw_add_card)
    add_summary = card_summary(raw_add_card)
    add_summary["quantity"] = 1
    add_summary["is_commander"] = False
    cards.append(add_summary)

    preview_context = {
        "deck_dir": context["deck_dir"],
        "card_count": sum(c.get("quantity", 1) for c in cards),
        "unique_card_count": len(cards),
        "not_found": [],
        "cards": cards,
    }

    tmp_dir = args.deck_dir / ".preview-tmp"
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "context.json").write_text(json.dumps(preview_context, indent=2))

    try:
        subprocess.run(
            [sys.executable, str(ANALYZE_SCRIPT), "--deck-dir", str(tmp_dir)],
            check=True, capture_output=True, text=True,
        )
        after_analysis = json.loads((tmp_dir / "analysis.json").read_text())
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    before_summary = before_analysis.get("curve_summary", {})
    after_summary = after_analysis.get("curve_summary", {})

    def delta(key):
        b, a = before_summary.get(key), after_summary.get(key)
        return None if b is None or a is None else round(a - b, 2)

    before_cats = before_analysis.get("categories", {})
    after_cats = after_analysis.get("categories", {})
    category_changes = {}
    for key in set(before_cats) | set(after_cats):
        b, a = set(before_cats.get(key, [])), set(after_cats.get(key, []))
        if a != b:
            category_changes[key] = {"added": sorted(a - b), "removed": sorted(b - a)}

    result = {
        "cut": args.cut,
        "add": args.add,
        "average_cmc_before": before_summary.get("average_cmc"),
        "average_cmc_after": after_summary.get("average_cmc"),
        "average_cmc_delta": delta("average_cmc"),
        "typical_average_cmc_before": before_summary.get("typical_average_cmc"),
        "typical_average_cmc_after": after_summary.get("typical_average_cmc"),
        "typical_average_cmc_delta": delta("typical_average_cmc"),
        "pct_cmc_le_3_delta": delta("pct_cmc_le_3"),
        "typical_pct_cmc_le_3_delta": delta("typical_pct_cmc_le_3"),
        "bracket_before": before_analysis["bracket_estimate"]["suggested"],
        "bracket_after": after_analysis["bracket_estimate"]["suggested"],
        "category_changes": category_changes,
    }

    out_path = args.deck_dir / "swap_preview.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
    print(
        f"Typical average CMC: {result['typical_average_cmc_before']} -> "
        f"{result['typical_average_cmc_after']} ({result['typical_average_cmc_delta']:+})"
    )
    if result["bracket_before"] != result["bracket_after"]:
        print(f"WARNING: bracket estimate would move: {result['bracket_before']} -> {result['bracket_after']}")


if __name__ == "__main__":
    main()
