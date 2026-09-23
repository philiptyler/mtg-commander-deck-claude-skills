"""Minimal stdlib client for Scryfall's /cards/search endpoint. Same
approach as upgrade-commander-deck's copy - duplicated rather than shared
so this skill stays independently installable. See that copy's docstring
for why this isn't an EDHREC integration.
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
            return []
        raise ScryfallSearchError(f"Scryfall returned {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}") from e

    return data.get("data", [])[:max_results]
