"""Snapshot a deck's current analysis.json/combos.json before applying
changes, so diff_after.py has a baseline to compare the post-change state
against. Safe to run even if one or both files don't exist yet.

Usage:
    python3 snapshot_before.py --deck-dir ../review-commander-deck/decks/my-deck
"""

import argparse
import shutil
from pathlib import Path

SNAPSHOT_FILES = ["analysis.json", "combos.json"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-dir", required=True, type=Path)
    args = ap.parse_args()

    tmp_dir = args.deck_dir / ".update-tmp"
    tmp_dir.mkdir(exist_ok=True)

    snapshotted = []
    for name in SNAPSHOT_FILES:
        src = args.deck_dir / name
        if src.exists():
            shutil.copy(src, tmp_dir / name)
            snapshotted.append(name)

    print(f"Snapshotted {snapshotted or '(nothing - no prior analysis/combos for this deck)'} to {tmp_dir}")


if __name__ == "__main__":
    main()
