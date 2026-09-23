"""Minimal stdlib client for Scryfall's /cards/search endpoint, used to
source upgrade candidates.

This is deliberately NOT an EDHREC integration. Scryfall computes its own
`edhrec_rank` per card (a global "how often is this played across all of
EDH" popularity figure) and exposes it as a sortable/filterable field on
its own, fully-documented, ToS-compliant search API - so candidate sourcing
never touches edhrec.com itself. `edhrec_rank` is a *global* popularity
signal, not commander-specific synergy, and this repo deliberately treats
it as a minor tiebreaker rather than the primary ranking factor - see
find_upgrade_candidates.py's scoring, and the note in SKILL.md about why.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.scryfall.com/cards/search"
USER_AGENT = "mtg-commander-deck-claude-skills/0.1 (github.com/philip; personal deck-review tool)"


class ScryfallSearchError(RuntimeError):
    pass


def search(query: str, max_results: int = 50) -> list:
    """Run a Scryfall search query, sorted by edhrec_rank ascending (most
    commonly played first). Returns a list of raw card dicts, capped at
    max_results (Scryfall paginates at 175/page; one page is always enough
    for our purposes).
    """
    params = urllib.parse.urlencode({"q": query, "order": "edhrec", "dir": "asc"})
    req = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []  # Scryfall returns 404 for a query with zero matches
        raise ScryfallSearchError(f"Scryfall returned {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}") from e

    return data.get("data", [])[:max_results]


def lookup_by_names(names: list) -> dict:
    """Batch-fetch exact cards by name via /cards/collection - used to get
    price/legality/oracle text for a short, already-decided list (e.g. combo
    completions from find_combo_completions.py), as opposed to search()'s
    broad query-based sourcing. Returns {name: card_dict} for names Scryfall
    could match; silently omits names it can't find."""
    if not names:
        return {}
    body = json.dumps({"identifiers": [{"name": n} for n in names]}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.scryfall.com/cards/collection",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ScryfallSearchError(f"Scryfall returned {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}") from e
    return {card["name"]: card for card in data.get("data", [])}
