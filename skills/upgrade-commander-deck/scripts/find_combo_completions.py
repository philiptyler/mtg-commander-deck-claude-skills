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
from find_upgrade_candidates import dominant_creature_type, is_tribal_match, normalize_card


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
    tribal_type = dominant_creature_type(context)

    # combo_count alone isn't enough to rank on - a combo can require every
    # listed card and STILL not actually loop without something else
    # entirely (an indestructible source, extra mana, a specific board
    # state) that Commander Spellbook tracks separately as
    # notable/easy prerequisites, not as a "card" in the combo. Missing
    # this was a direct, concrete mistake: Raptor Hatchling + Warstorm
    # Surge was presented as a clean combo completion, but the actual
    # variant's notablePrerequisites read "You have a way to give Raptor
    # Hatchling indestructible" - without that (a fourth thing, not itself
    # a listed card), a 1-toughness creature dies on the first damage
    # instance and the "loop" is a single activation. free_combo_count
    # (no notable/easy prerequisites at all) is tracked separately and
    # ranked above raw combo_count for exactly this reason.
    groups = defaultdict(lambda: {"combo_count": 0, "free_combo_count": 0, "produces": set(),
                                   "combo_urls": [], "prerequisites": []})
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
        notable = combo.get("notable_prerequisites")
        easy = combo.get("easy_prerequisites")
        if notable or easy:
            g["prerequisites"].append({"url": combo["url"], "notable": notable, "easy": easy})
        else:
            g["free_combo_count"] += 1

    # Look up every grouped name (not just a top-N-by-combo-count slice)
    # before ranking, not after - otherwise an on-tribe card with a lower
    # combo_count could get cut before it ever has a chance to out-rank an
    # off-tribe card once tribal_match is factored in below. Found via
    # direct feedback: Hornet Nest (an Insect) got recommended to a
    # Dinosaur tribal deck ahead of any on-tribe alternative, in part
    # because ranking only ever considered combo_count.
    lookup = scryfall_search_client.lookup_by_names(list(groups))

    results = []
    for name, g in groups.items():
        card = lookup.get(name)
        if card is None:
            continue  # couldn't resolve the exact name (rare)
        card = normalize_card(card)
        usd = (card.get("prices") or {}).get("usd")
        if args.budget is not None and usd is not None and float(usd) > args.budget:
            continue
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
            "free_combo_count": g["free_combo_count"],
            "prerequisites": g["prerequisites"],
            "produces": sorted(g["produces"]),
            "combo_urls": g["combo_urls"],
            "tribal_match": is_tribal_match(card, tribal_type),
        })

    # On-tribe first (see docstring on why, and find_upgrade_candidates.py's
    # identical reasoning), then by free_combo_count (a completion with NO
    # extra prerequisites - see the docstring above on why that's a
    # meaningfully different, more reliable thing than combo_count alone),
    # then by raw combo_count as the last tiebreaker.
    results.sort(key=lambda r: (not r["tribal_match"], -r["free_combo_count"], -r["combo_count"]))
    results = results[: args.count]

    out_path = args.deck_dir / "combo_completion_candidates.json"
    out_path.write_text(json.dumps({"tribal_type": tribal_type, "candidates": results}, indent=2))
    print(f"Wrote {out_path} ({len(results)} candidates)")
    for r in results[:5]:
        tribe_note = " [on-tribe]" if r["tribal_match"] else ""
        free_note = "" if r["free_combo_count"] == r["combo_count"] else (
            f" ({r['free_combo_count']}/{r['combo_count']} free of extra prerequisites - "
            f"see 'prerequisites' for the rest)"
        )
        print(f"  {r['name']}{tribe_note} - completes {r['combo_count']} combo(s){free_note}: {r['produces']}")


if __name__ == "__main__":
    main()
