"""Surface cards that complete a combo already one card deep in this deck,
regardless of category. This is a stronger, more direct win-condition
signal than any category-based text search in find_upgrade_candidates.py,
and it shouldn't depend on luck (guessing the right category to search)
to be found - that's exactly how this script came to exist: sourcing
"protection" candidates for the dinos deck happened to surface Sword of
Feast and Famine, which completes an infinite-combat-phases combo with
Aggravated Assault already in that deck. A deck can have dozens of
one-card-away combos; most are coincidental, but a card that completes
*multiple* separately-cataloged combos is a real, deterministic quality
signal, not a coincidence - that's what this ranks on.

Usage:
    python3 find_combo_completions.py --deck-dir ../review-commander-deck/decks/my-deck --count 10
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scryfall_search_client
from find_upgrade_candidates import normalize_card


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--budget", type=float, default=None, help="drop candidates over this USD price")
    args = ap.parse_args()

    combos_path = args.deck_dir / "combos.json"
    if not combos_path.exists():
        print("No combos.json for this deck - run find-deck-combos first.")
        return

    combos = json.loads(combos_path.read_text())
    context = json.loads((args.deck_dir / "context.json").read_text())
    existing_names = {c["name"] for c in context["cards"]}

    groups = defaultdict(lambda: {"combo_count": 0, "produces": set(), "combo_urls": []})
    for combo in combos.get("almost_included", []):
        if len(combo["missing_cards"]) != 1:
            continue
        name = combo["missing_cards"][0]
        if name in existing_names:
            continue  # shouldn't happen (it's "missing"), but be defensive
        g = groups[name]
        g["combo_count"] += 1
        g["produces"] |= set(combo["produces"])
        g["combo_urls"].append(combo["url"])

    ranked_names = sorted(groups, key=lambda n: -groups[n]["combo_count"])
    lookup = scryfall_search_client.lookup_by_names(ranked_names[: max(args.count * 3, 30)])

    results = []
    for name in ranked_names:
        card = lookup.get(name)
        if card is None:
            continue  # couldn't resolve the exact name (rare)
        card = normalize_card(card)
        usd = (card.get("prices") or {}).get("usd")
        if args.budget is not None and usd is not None and float(usd) > args.budget:
            continue
        g = groups[name]
        results.append({
            "name": name,
            "mana_cost": card.get("mana_cost"),
            "cmc": card.get("cmc"),
            "type_line": card.get("type_line"),
            "oracle_text": card.get("oracle_text"),
            "color_identity": card.get("color_identity"),
            "usd": usd,
            "game_changer": card.get("game_changer", False),
            "combo_count": g["combo_count"],
            "produces": sorted(g["produces"]),
            "combo_urls": g["combo_urls"],
        })
        if len(results) >= args.count:
            break

    out_path = args.deck_dir / "combo_completion_candidates.json"
    out_path.write_text(json.dumps({"candidates": results}, indent=2))
    print(f"Wrote {out_path} ({len(results)} candidates)")
    for r in results[:5]:
        print(f"  {r['name']} - completes {r['combo_count']} combo(s): {r['produces']}")


if __name__ == "__main__":
    main()
