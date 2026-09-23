"""Parse a plain-text Commander decklist (Moxfield/Archidekt export style)
into a list of {quantity, name, is_commander} entries.

Handles lines like:
    1 Sol Ring
    1x Sol Ring
    1 Sol Ring (C21) 263
    1 Krenko, Mob Boss *CMDR*
    1x Ephemerate (h1r) 1 *F* [Blink]
    1x Pantlaza, Sun-Favored (lcc) 4 [Commander{top}]
Trailing set/collector-number info, foil markers (*F*), and bracketed
category tags ([Finisher], [Commander{top}], ...) are all stripped from the
name. A card is treated as the commander if it carries a *CMDR*/*commander*
marker or a bracketed tag containing "commander" (case-insensitive).

Skips blank lines, comment lines (// ...), and section headers that don't
start with a quantity (e.g. "Commander", "Deck", "Sideboard").
"""

import argparse
import json
import re
from pathlib import Path

HEAD_RE = re.compile(r"^\s*(?P<qty>\d+)\s*x?\s+(?P<rest>.+?)\s*$")
TRAILING_TAG_RE = re.compile(r"\[([^\]]*)\]\s*$")
COMMANDER_MARKER_RE = re.compile(r"\*cmdr\*|\*commander\*", re.IGNORECASE)
TRAILING_STAR_MARKER_RE = re.compile(r"\*[A-Za-z]+\*\s*$")
TRAILING_SET_COLLECTOR_RE = re.compile(r"\s*\([A-Za-z0-9]{2,6}\)\s*[A-Za-z0-9\-★]*\s*$")


def parse_line(line: str):
    line = line.strip()
    if not line or line.startswith("//") or line.startswith("#"):
        return None

    head = HEAD_RE.match(line)
    if not head:
        return None

    rest = head.group("rest")
    is_commander = False

    # Bracketed category tag, e.g. "[Finisher]" or "[Commander{top}]".
    tag_match = TRAILING_TAG_RE.search(rest)
    if tag_match:
        if "commander" in tag_match.group(1).lower():
            is_commander = True
        rest = rest[: tag_match.start()].strip()

    # *CMDR*/*commander* marker, anywhere in what's left.
    if COMMANDER_MARKER_RE.search(rest):
        is_commander = True
        rest = COMMANDER_MARKER_RE.sub("", rest).strip()

    # Any other trailing *X* marker (e.g. *F* for foil).
    rest = TRAILING_STAR_MARKER_RE.sub("", rest).strip()

    # Trailing (SET) collector# info.
    rest = TRAILING_SET_COLLECTOR_RE.sub("", rest).strip()

    return {
        "quantity": int(head.group("qty")),
        "name": rest,
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
