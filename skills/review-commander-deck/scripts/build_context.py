"""Merge a deck's decklist quantities with cached Scryfall data into one
context.json file — the single source of truth for downstream analysis.

Usage:
    python3 build_context.py --deck-dir decks/my-deck
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_decklist import parse_decklist
import scryfall_client

SKILL_ROOT = Path(__file__).resolve().parent.parent

# Fields pulled from the raw Scryfall card object into context.json. Keeping
# this an explicit allowlist (rather than dumping the whole card) keeps
# context.json small and focused on what analyze_deck.py / the review
# actually needs.
FIELDS = [
    "name", "mana_cost", "cmc", "type_line", "oracle_text",
    "color_identity", "colors", "game_changer",
    "power", "toughness", "loyalty", "keywords", "produced_mana",
]


def card_summary(card: dict) -> dict:
    summary = {field: card.get(field) for field in FIELDS}
    summary["commander_legal"] = card.get("legalities", {}).get("commander")
    return summary


def build_context(deck_dir: Path, cache_dir: Path) -> dict:
    decklist_path = deck_dir / "decklist.txt"
    entries = parse_decklist(decklist_path.read_text())
    names = [e["name"] for e in entries]

    cards, not_found = scryfall_client.get_cards(names, cache_dir)

    context_cards = []
    for entry in entries:
        card = cards.get(entry["name"])
        if card is None:
            context_cards.append({
                "name": entry["name"],
                "quantity": entry["quantity"],
                "is_commander": entry["is_commander"],
                "not_found": True,
            })
            continue
        summary = card_summary(card)
        summary["quantity"] = entry["quantity"]
        summary["is_commander"] = entry["is_commander"]
        context_cards.append(summary)

    return {
        "deck_dir": deck_dir.name,
        "card_count": sum(e["quantity"] for e in entries),
        "unique_card_count": len(entries),
        "not_found": not_found,
        "cards": context_cards,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    ap.add_argument("--cache-dir", type=Path, default=SKILL_ROOT / "cache" / "scryfall")
    args = ap.parse_args()

    context = build_context(args.deck_dir, args.cache_dir)
    out_path = args.deck_dir / "context.json"
    out_path.write_text(json.dumps(context, indent=2))
    print(
        f"Wrote {out_path} "
        f"({context['card_count']} cards, {len(context['not_found'])} not found)"
    )


if __name__ == "__main__":
    main()
