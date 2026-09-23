"""Parse a plain-text Commander decklist (Moxfield/Archidekt export style)
into a list of {quantity, name, is_commander} entries.

Handles lines like:
    1 Sol Ring
    1x Sol Ring
    1 Sol Ring (C21) 263
    1 Krenko, Mob Boss *CMDR*
Skips blank lines, comment lines (// ...), and section headers that don't
start with a quantity (e.g. "Commander", "Deck", "Sideboard").
"""

import argparse
import json
import re
from pathlib import Path

LINE_RE = re.compile(
    r"""^\s*
    (?P<qty>\d+)\s*x?\s+           # quantity, optional trailing 'x'
    (?P<name>.+?)                   # card name (non-greedy)
    (?:\s*\([A-Za-z0-9]{2,6}\)\s*[A-Za-z0-9\-★]*)?  # optional trailing (SET) collector#
    \s*$
    """,
    re.VERBOSE,
)

COMMANDER_MARKERS = ("*cmdr*", "*commander*")


def parse_line(line: str):
    line = line.strip()
    if not line or line.startswith("//") or line.startswith("#"):
        return None

    is_commander = False
    for marker in COMMANDER_MARKERS:
        if marker in line.lower():
            is_commander = True
            line = re.sub(re.escape(marker), "", line, flags=re.IGNORECASE).strip()

    match = LINE_RE.match(line)
    if not match:
        return None

    name = match.group("name").strip()
    return {
        "quantity": int(match.group("qty")),
        "name": name,
        "is_commander": is_commander,
    }


def parse_decklist(text: str):
    entries = []
    for raw_line in text.splitlines():
        entry = parse_line(raw_line)
        if entry:
            entries.append(entry)
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("decklist_path", type=Path)
    args = ap.parse_args()
    print(json.dumps(parse_decklist(args.decklist_path.read_text()), indent=2))


if __name__ == "__main__":
    main()
