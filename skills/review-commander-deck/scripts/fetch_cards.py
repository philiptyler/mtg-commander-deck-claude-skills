"""Ensure every card in a deck's decklist.txt is fetched from Scryfall and
cached locally. Run this before build_context.py.

Usage:
    python3 fetch_cards.py --deck-dir decks/my-deck
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_decklist import parse_decklist
import scryfall_client

SKILL_ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    ap.add_argument("--cache-dir", type=Path, default=SKILL_ROOT / "cache" / "scryfall")
    args = ap.parse_args()

    decklist_path = args.deck_dir / "decklist.txt"
    entries = parse_decklist(decklist_path.read_text())
    names = [e["name"] for e in entries]
    unique_count = len(dict.fromkeys(names))

    _, not_found = scryfall_client.get_cards(names, args.cache_dir)

    print(f"Fetched/cached {unique_count - len(not_found)}/{unique_count} unique cards.")
    if not_found:
        print("NOT FOUND on Scryfall (check spelling in decklist.txt):")
        for n in not_found:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
