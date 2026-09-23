"""Minimal stdlib client for Commander Spellbook's /find-my-combos endpoint.

Unlike EDHREC, Commander Spellbook is open source (MIT) and its API is
meant for exactly this kind of programmatic use - see
https://backend.commanderspellbook.com/schema/swagger/. No auth needed for
find-my-combos. Published guidance: name your client in the User-Agent,
stay under ~80 requests/minute (a single deck lookup is one request, so
this is a non-issue for how this skill uses it).

No third-party dependencies (urllib only), matching the rest of this repo.
"""

import json
import urllib.error
import urllib.request

API_URL = "https://backend.commanderspellbook.com/find-my-combos?groupByCombo=true"
USER_AGENT = "mtg-commander-deck-claude-skills/0.1 (github.com/philip; personal deck-review tool)"


class SpellbookError(RuntimeError):
    pass


def _simplify_combo(combo: dict, submitted_names: set) -> dict:
    card_names = [u["card"]["name"] for u in combo.get("uses", [])]
    missing = [n for n in card_names if n not in submitted_names]
    return {
        "id": combo.get("id"),
        "url": f"https://commanderspellbook.com/combo/{combo.get('id')}/",
        "cards": card_names,
        "missing_cards": missing,
        "produces": [p["feature"]["name"] for p in combo.get("produces", [])],
        "notes": combo.get("notes") or None,
        "easy_prerequisites": combo.get("easyPrerequisites") or None,
        "notable_prerequisites": combo.get("notablePrerequisites") or None,
        "bracket_tag": combo.get("bracketTag"),
        "popularity": combo.get("popularity"),
        "color_identity": combo.get("identity"),
    }


def find_combos(commander_names, other_card_names):
    """Look up combos for a deck's card pool.

    Returns {"included": [...], "almost_included": [...]} - "included" are
    combos every piece of which is already in the deck; "almost_included"
    are combos missing one or more pieces (see each entry's
    "missing_cards"). Both are simplified/trimmed for readability - the
    raw API response includes full Scryfall image URIs per card, which
    aren't useful here.
    """
    body = json.dumps({
        "commanders": [{"card": name} for name in commander_names],
        "main": [{"card": name} for name in other_card_names],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SpellbookError(f"Commander Spellbook returned {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}") from e

    results = data.get("results", {})
    submitted = set(commander_names) | set(other_card_names)
    return {
        "included": [_simplify_combo(c, submitted) for c in results.get("included", [])],
        "almost_included": [_simplify_combo(c, submitted) for c in results.get("almostIncluded", [])],
    }
