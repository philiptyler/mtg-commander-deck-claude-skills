"""Source and deterministically rank nonbasic land candidates that produce
a specific color, for filling a shortfall found by mana_base_analysis.py.

Usage:
    python3 find_land_candidates.py --deck-dir ../review-commander-deck/decks/my-deck --color G --count 10
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scryfall_search_client

TAPPED_RE = re.compile(r"enters (the battlefield )?tapped")
TAPPED_UPSIDE_HINTS = ["unless", "if you don't", "scry", "surveil", "gain 1 life", "gain life", "draw a card"]


# Same fix as upgrade-commander-deck's find_upgrade_candidates.py: modal-DFC
# lands (e.g. pathways) leave oracle_text null at the top level of a raw
# Scryfall search result - the real text lives in card_faces. produced_mana
# is unaffected (Scryfall computes that at the top level regardless), but
# enters_tapped_no_upside and any manual read of the card's text would see
# nothing without this.
def normalize_card(card: dict) -> dict:
    faces = card.get("card_faces") or []
    if not card.get("oracle_text") and faces:
        card = dict(card)
        card["oracle_text"] = "\n".join(f.get("oracle_text", "") for f in faces if f.get("oracle_text"))
    return card


def commander_color_identity(context: dict) -> list:
    colors = set()
    for card in context["cards"]:
        if card.get("is_commander"):
            colors |= set(card.get("color_identity") or [])
    return sorted(colors)


def enters_tapped_no_upside(oracle_text: str) -> bool:
    text = (oracle_text or "").lower()
    if not TAPPED_RE.search(text):
        return False
    return not any(hint in text for hint in TAPPED_UPSIDE_HINTS)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    ap.add_argument("--color", required=True, choices=list("WUBRG"), help="the shortfall color to fix")
    ap.add_argument("--count", type=int, default=10)
    ap.add_argument("--budget", type=float, default=None, help="max USD price per card")
    ap.add_argument("--prefer-untapped", action="store_true", help="deprioritize always-enters-tapped lands (use for Tier 1-2 shortfalls)")
    args = ap.parse_args()

    context = json.loads((args.deck_dir / "context.json").read_text())
    color_identity = commander_color_identity(context)
    existing_names = {c["name"] for c in context["cards"]}

    query_parts = [f"id<={''.join(color_identity) or 'c'}", "t:land", "-is:funny"]
    if args.budget is not None:
        query_parts.append(f"usd<={args.budget}")
    query = " ".join(query_parts)

    raw_cards = scryfall_search_client.search(query, max_results=80)

    candidates = []
    for card in raw_cards:
        card = normalize_card(card)
        if card.get("name") in existing_names:
            continue
        produced = set(card.get("produced_mana") or [])
        if args.color not in produced:
            continue
        candidates.append({
            "name": card["name"],
            "type_line": card.get("type_line"),
            "oracle_text": card.get("oracle_text"),
            "produced_mana": sorted(produced),
            "usd": (card.get("prices") or {}).get("usd"),
            "edhrec_rank": card.get("edhrec_rank"),
            "enters_tapped_no_upside": enters_tapped_no_upside(card.get("oracle_text")),
        })

    candidates.sort(key=lambda c: (
        c["enters_tapped_no_upside"] if args.prefer_untapped else False,
        c["edhrec_rank"] if c["edhrec_rank"] is not None else 10**9,
    ))
    candidates = candidates[: args.count]

    result = {"color": args.color, "query": query, "candidates": candidates}
    out_path = args.deck_dir / f"land_candidates_{args.color}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path} ({len(candidates)} candidates)")


if __name__ == "__main__":
    main()
