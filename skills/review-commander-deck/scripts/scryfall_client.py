"""Minimal stdlib client for Scryfall's card collection endpoint, with a
disk-backed cache so re-running a deck never re-fetches a card it already has.

No third-party dependencies (urllib only) so this skill works with zero
install step. Scryfall requires a descriptive User-Agent and Accept header —
requests without one are rejected with 403.

Docs: https://scryfall.com/docs/api/cards/collection
"""

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.scryfall.com/cards/collection"
USER_AGENT = "mtg-commander-deck-claude-skills/0.1 (github.com/philip; personal deck-review tool)"
BATCH_SIZE = 75  # Scryfall's max identifiers per collection request
REQUEST_DELAY_SECONDS = 0.1  # be polite between batches, per Scryfall's rate-limit guidance


class ScryfallError(RuntimeError):
    pass


def _slugify(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "unknown"


def _cache_path(cache_dir: Path, name: str) -> Path:
    return cache_dir / f"{_slugify(name)}.json"


def _query_identifier(name: str) -> str:
    # Scryfall's /cards/collection only matches double-faced/split/pathway
    # cards by their front-face name, even though decklist exports (and
    # Scryfall's own /cards/named) use the combined "Front // Back" form.
    return name.split(" // ", 1)[0].strip()


def _load_cached(cache_dir: Path, names):
    found, missing = {}, []
    for name in names:
        path = _cache_path(cache_dir, name)
        if path.exists():
            found[name] = json.loads(path.read_text())
        else:
            missing.append(name)
    return found, missing


def _fetch_batch(names):
    body = json.dumps({"identifiers": [{"name": n} for n in names]}).encode("utf-8")
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
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ScryfallError(f"Scryfall returned {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')}") from e


def get_cards(names, cache_dir):
    """Return (cards, not_found) for the given card names.

    cards: {requested_name: scryfall_card_dict}, using disk cache where
        possible and batching the rest through /cards/collection.
    not_found: list of requested names Scryfall couldn't match at all.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    unique_names = list(dict.fromkeys(names))  # de-dupe, preserve order
    result, missing = _load_cached(cache_dir, unique_names)
    not_found = []

    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i : i + BATCH_SIZE]
        query_map = {_query_identifier(n): n for n in batch}
        data = _fetch_batch(list(query_map.keys()))
        for card in data.get("data", []):
            result[card["name"]] = card
            _cache_path(cache_dir, card["name"]).write_text(json.dumps(card, indent=2))
        for nf in data.get("not_found", []):
            queried = nf.get("name", "<unknown>")
            not_found.append(query_map.get(queried, queried))
        if i + BATCH_SIZE < len(missing):
            time.sleep(REQUEST_DELAY_SECONDS)

    # Re-key onto the caller's original spelling (case/whitespace) where the
    # canonical Scryfall name differs slightly from what was in the decklist.
    by_lower = {k.lower(): v for k, v in result.items()}
    final = {}
    for name in unique_names:
        if name in result:
            final[name] = result[name]
        elif name.lower() in by_lower:
            final[name] = by_lower[name.lower()]
    return final, not_found
