"""Check an already-reviewed deck's card pool against Commander Spellbook's
combo database: what combos are already fully in the deck, and what combos
are one or two cards away.

Requires review-commander-deck's context.json to already exist for this
deck - run that skill's pipeline first if it doesn't.

Usage:
    python3 find_combos.py --deck-dir ../review-commander-deck/decks/my-deck
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import spellbook_client


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    args = ap.parse_args()

    context = json.loads((args.deck_dir / "context.json").read_text())

    commanders = [c["name"] for c in context["cards"] if c.get("is_commander")]
    others = [c["name"] for c in context["cards"] if not c.get("is_commander") and not c.get("not_found")]

    result = spellbook_client.find_combos(commanders, others)

    out_path = args.deck_dir / "combos.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
    print(f"Combos already in the deck: {len(result['included'])}")
    print(f"Combos one or more cards away: {len(result['almost_included'])}")


if __name__ == "__main__":
    main()
